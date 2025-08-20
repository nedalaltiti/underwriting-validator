"""
Duplication Repository for database operations.

This repository handles duplication validation by checking if a contact's SSN or phone number
already exists in the system under certain status conditions.
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, null, bindparam, not_

from underwriting_validation.db.models import Contact, ContactCategory, ContactLeadStatus
from underwriting_validation.config.settings import settings

logger = logging.getLogger(__name__)

class DuplicationRepository:
    """Repository for duplication validation operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Get duplication-specific field values from settings
        self.exclude_contact_id = settings.duplication_fields.exclude_contact_id
    
    async def check_ssn_duplication(self, ssn: str, exclude_contact_id: int = None) -> List[Dict[str, Any]]:
        """
        Check if SSN already exists in the system under certain status conditions.
        
        Args:
            ssn: The SSN to check for duplication
            exclude_contact_id: Contact ID to exclude from the check (defaults to settings value)
            
        Returns:
            List of contacts with matching SSN that meet the duplication criteria
        """
        try:
            if exclude_contact_id is None:
                exclude_contact_id = self.exclude_contact_id
            
            # Define excluded lead status titles
            excluded_statuses = [
                'Graduated/Completed Program', 
                'Graduated', 
                'Cancelled', 
                'Dropped/Cancelled', 
                'Force Cancel NSF'
            ]
            
            stmt = (
                select(
                    Contact.id,
                    Contact.ssn,
                    Contact.acctid,
                    ContactCategory.title.label('contact_categorie'),
                    ContactLeadStatus.title.label('contacts_lead_status')
                )
                .select_from(Contact)
                .outerjoin(ContactLeadStatus, Contact.leadstatus == ContactLeadStatus.id)
                .outerjoin(ContactCategory, Contact.c_type == ContactCategory.id)
                .where(
                    and_(
                        Contact.ssn == ssn,
                        Contact.id != exclude_contact_id,
                        # Base conditions are already checked by eligibility check
                        # Exclude certain lead status titles
                        not_(ContactLeadStatus.title.in_(excluded_statuses))
                    )
                )
            )
            
            result = await self.session.execute(stmt)
            duplicates = []
            
            for row in result.fetchall():
                duplicates.append({
                    "id": row.id,
                    "ssn": row.ssn,
                    "acctid": row.acctid,
                    "contact_categorie": row.contact_categorie,
                    "contacts_lead_status": row.contacts_lead_status
                })
            
            logger.info(f"SSN duplication check for SSN ending in ***{ssn[-4:]} found {len(duplicates)} duplicates")
            return duplicates
            
        except Exception as e:
            logger.error(f"Error checking SSN duplication for SSN ending in ***{ssn[-4:]}: {e}")
            raise
    
    async def check_phone_duplication(self, phone: str, exclude_contact_id: int = None) -> List[Dict[str, Any]]:
        """
        Check if phone number already exists in the system under certain status conditions.
        
        Args:
            phone: The phone number to check for duplication
            exclude_contact_id: Contact ID to exclude from the check (defaults to settings value)
            
        Returns:
            List of contacts with matching phone number that meet the duplication criteria
        """
        try:
            if exclude_contact_id is None:
                exclude_contact_id = self.exclude_contact_id
            
            # Define excluded lead status titles
            excluded_statuses = [
                'Graduated/Completed Program', 
                'Graduated', 
                'Cancelled', 
                'Dropped/Cancelled', 
                'Force Cancel NSF'
            ]
            
            stmt = (
                select(
                    Contact.id,
                    Contact.phone3,
                    Contact.acctid,
                    ContactCategory.title.label('contact_categorie'),
                    ContactLeadStatus.title.label('contacts_lead_status')
                )
                .select_from(Contact)
                .outerjoin(ContactLeadStatus, Contact.leadstatus == ContactLeadStatus.id)
                .outerjoin(ContactCategory, Contact.c_type == ContactCategory.id)
                .where(
                    and_(
                        Contact.phone3 == phone,
                        Contact.id != exclude_contact_id,
                        # Base conditions are already checked by eligibility check
                        # Exclude certain lead status titles
                        not_(ContactLeadStatus.title.in_(excluded_statuses))
                    )
                )
            )
            
            result = await self.session.execute(stmt)
            duplicates = []
            
            for row in result.fetchall():
                duplicates.append({
                    "id": row.id,
                    "phone3": row.phone3,
                    "acctid": row.acctid,
                    "contact_categorie": row.contact_categorie,
                    "contacts_lead_status": row.contacts_lead_status
                })
            
            logger.info(f"Phone duplication check for phone ending in ***{phone[-4:]} found {len(duplicates)} duplicates")
            return duplicates
            
        except Exception as e:
            logger.error(f"Error checking phone duplication for phone ending in ***{phone[-4:]}: {e}")
            raise
    
    async def check_contact_duplication(self, contact_id: int, exclude_contact_id: int = None) -> Dict[str, Any]:
        """
        Check for duplication of a contact's SSN and phone number.
        
        Args:
            contact_id: The contact ID to check for duplication
            exclude_contact_id: Contact ID to exclude from the check (defaults to settings value)
            
        Returns:
            Dictionary containing duplication check results for both SSN and phone
        """
        try:
            if exclude_contact_id is None:
                exclude_contact_id = self.exclude_contact_id
            
            # First get the contact's SSN and phone
            stmt = select(Contact.ssn, Contact.phone3).where(Contact.id == contact_id)
            result = await self.session.execute(stmt)
            contact_data = result.fetchone()
            
            if not contact_data:
                logger.warning(f"Contact {contact_id} not found for duplication check")
                return {
                    "contact_id": contact_id,
                    "ssn_duplicates": [],
                    "phone_duplicates": [],
                    "has_duplicates": False,
                    "error": "Contact not found"
                }
            
            ssn = contact_data.ssn
            phone = contact_data.phone3
            
            # Check SSN duplication
            ssn_duplicates = []
            if ssn:
                ssn_duplicates = await self.check_ssn_duplication(ssn, exclude_contact_id)
            
            # Check phone duplication
            phone_duplicates = []
            if phone:
                phone_duplicates = await self.check_phone_duplication(phone, exclude_contact_id)
            
            has_duplicates = len(ssn_duplicates) > 0 or len(phone_duplicates) > 0
            
            return {
                "contact_id": contact_id,
                "ssn": ssn,
                "phone": phone,
                "ssn_duplicates": ssn_duplicates,
                "phone_duplicates": phone_duplicates,
                "has_duplicates": has_duplicates,
                "ssn_duplicate_count": len(ssn_duplicates),
                "phone_duplicate_count": len(phone_duplicates)
            }
            
        except Exception as e:
            logger.error(f"Error checking contact duplication for contact {contact_id}: {e}")
            raise

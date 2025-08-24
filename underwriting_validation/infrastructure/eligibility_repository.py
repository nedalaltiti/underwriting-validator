"""
Eligibility Repository for contact eligibility checks.

This repository handles contact eligibility validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, bindparam
from underwriting_validation.db.models import Contact, ContactCategory, ContactLeadStatus
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class EligibilityRepository:
    """Repository for contact eligibility checks."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_contact_eligibility(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Check if a contact is eligible for validation process."""
        masked_id = mask_contact_id(contact_id)
        logger.debug(f"Executing eligibility check query for contact {masked_id}")
        
        # First, get the contact data to check individual criteria
        contact_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.email,
                Contact.phone3,
                Contact.del_,
                Contact.iscoapp,
                func.coalesce(ContactCategory.title, 'Unknown').label('contact_category'),
                func.coalesce(ContactLeadStatus.title, 'Unknown').label('contact_lead_status')
            )
            .select_from(Contact)
            .outerjoin(ContactCategory, ContactCategory.id == Contact.c_type)
            .outerjoin(ContactLeadStatus, ContactLeadStatus.id == Contact.leadstatus)
            .where(Contact.id == bindparam('contact_id'))
        )
        
        result = await self.session.execute(contact_stmt, {"contact_id": contact_id})
        row = result.fetchone()
        
        if not row:
            return {
                "contact_id": contact_id,
                "eligible": False,
                "reason": "Contact not found in database"
            }
        
        # Check each eligibility criterion
        reasons = []
        
        if row.acctid == 5783:
            reasons.append("Contact is in company type 5783 (CDR clients only)")
        
        if row.contact_category != 'Underwriting':
            reasons.append(f"Contact is not in underwriting stage (current: {row.contact_category})")
        
        if row.del_ == True:
            reasons.append("Contact is deleted")
        
        if row.iscoapp == 1:
            reasons.append("Contact is a co-applicant")
        
        if row.contact_lead_status != 'Submitted':
            reasons.append(f"Contact is not in submitted status (current: {row.contact_lead_status})")
        
        if reasons:
            logger.debug(f"Contact {masked_id} eligibility check failed: {', '.join(reasons)}")
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "email": row.email,
                "phone3": row.phone3,
                "del_flag": row.del_,
                "iscoapp": row.iscoapp,
                "contact_category": row.contact_category,
                "contact_lead_status": row.contact_lead_status,
                "eligible": False,
                "reason": "; ".join(reasons)
            }
        
        logger.debug(f"Contact {masked_id} eligibility check passed: category={row.contact_category}, status={row.contact_lead_status}")
        return {
            "contact_id": row.id,
            "acctid": row.acctid,
            "email": row.email,
            "phone3": row.phone3,
            "del_flag": row.del_,
            "iscoapp": row.iscoapp,
            "contact_category": row.contact_category,
            "contact_lead_status": row.contact_lead_status,
            "eligible": True,
            "reason": "Contact meets all eligibility criteria"
        }

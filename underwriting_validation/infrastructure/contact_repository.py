"""
Contact Repository for database operations.

This repository holds a single database session and provides data access methods
for contact-related operations. It ensures consistent transactions and efficient
connection pool usage.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, bindparam, and_, or_, null
from underwriting_validation.db.models import Contact, ContactUserField, BudgetData, BudgetFields, Company, ContactCategory, ContactLeadStatus
from underwriting_validation.config.settings import settings
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContactRepository:
    """Repository for contact-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Get field IDs from settings
        self.financial_hardship_id = settings.hardship_fields.financial_hardship_id
        self.hardship_description_id = settings.hardship_fields.hardship_description_id
        
        # Get budget field values from settings
        self.budget_acctid = settings.budget_fields.acctid
        self.budget_c_type = settings.budget_fields.c_type
        self.budget_iscoapp = settings.budget_fields.iscoapp
        self.budget_leadstatus = settings.budget_fields.leadstatus
        
        # Get address field values from settings
        self.address_acctid = settings.address_fields.acctid
        self.address_c_type = settings.address_fields.c_type
        self.address_iscoapp = settings.address_fields.iscoapp
        self.address_leadstatus = settings.address_fields.leadstatus
        self.address_company_type = settings.address_fields.company_type
    
    async def fetch_contact(self, contact_id: int) -> Optional[Contact]:
        """Fetch a single contact by ID with soft-delete filtering."""
        stmt = (
            select(Contact)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter: not deleted (del IS NULL OR del != true)
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    )
                )
            )
        )
        
        result = await self.session.execute(stmt, {"contact_id": contact_id})
        return result.scalar_one_or_none()
    
    async def fetch_contact_with_budget_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with budget data using a single query."""
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.del_,
                Contact.iscoapp,
                Contact.c_type,
                Contact.leadstatus,
                func.sum(
                    case(
                        (BudgetFields.field_type == 'I', BudgetData.field_val),
                        else_=0
                    )
                ).label('total_net_income'),
                func.sum(
                    case(
                        (BudgetFields.field_type == 'E', BudgetData.field_val),
                        else_=0
                    )
                ).label('total_expenses')
            )
            .select_from(Contact)
            .outerjoin(BudgetData, Contact.id == BudgetData.contact_id)
            .outerjoin(BudgetFields, BudgetData.field_id == BudgetFields.id)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    ),
                    # Additional filters from environment variables
                    Contact.acctid == self.budget_acctid,
                    Contact.c_type == self.budget_c_type,
                    Contact.iscoapp == self.budget_iscoapp,
                    Contact.leadstatus == self.budget_leadstatus
                )
            )
            .group_by(
                Contact.id, 
                Contact.acctid, 
                Contact.del_, 
                Contact.iscoapp, 
                Contact.c_type, 
                Contact.leadstatus
            )
        )
        
        result = await self.session.execute(stmt, {"contact_id": contact_id})
        row = result.fetchone()
        
        if row:
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "del_flag": row.del_,
                "iscoapp": row.iscoapp,
                "c_type": row.c_type,
                "leadstatus": row.leadstatus,
                "total_net_income": float(row.total_net_income or 0),
                "total_expenses": float(row.total_expenses or 0),
            }
        return None
    
    async def fetch_contact_with_hardship_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with hardship data using a single query."""
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.del_,
                Contact.iscoapp,
                Contact.c_type,
                Contact.leadstatus,
                func.max(case(
                    (ContactUserField.custom_id == self.financial_hardship_id, 
                     ContactUserField.f_string)
                )).label('financial_hardship'),
                func.max(case(
                    (ContactUserField.custom_id == self.hardship_description_id, 
                     ContactUserField.f_string)
                )).label('hardship_description')
            )
            .outerjoin(ContactUserField, Contact.id == ContactUserField.contact_id)
            .where(Contact.id == contact_id)
            .group_by(
                Contact.id,
                Contact.acctid,
                Contact.del_,
                Contact.iscoapp,
                Contact.c_type,
                Contact.leadstatus
            )
        )
        
        result = await self.session.execute(stmt)
        row = result.fetchone()
        
        if row:
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "del": row.del_,
                "iscoapp": row.iscoapp,
                "c_type": row.c_type,
                "leadstatus": row.leadstatus,
                "financial_hardship": row.financial_hardship,
                "hardship_description": row.hardship_description,
            }
        return None
    
    async def fetch_contact_with_address_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with address validation data using the provided SQL query."""
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.state,
                Company.name.label('assigned_company'),
                case(
                    # Clarity Debt Resolution, Inc. (company_ids: 26267, 87758)
                    (and_(
                        Contact.company_id.in_([26267, 87758]),
                        Contact.state.in_(['AL','AK','AZ','AR','CA','CO','DC','FL','ID','IN','KY','MD',
                                         'MA','MI','MN','MS','MO','MT','NE','NM','NY','NC','OH','OK',
                                         'SD','TN','TX','UT'])
                    ), 'Match'),
                    # Concordia Legal Advisors, PLLC (company_ids: 83850, 89302, 67264)
                    (and_(
                        Contact.company_id.in_([83850, 89302, 67264]),
                        Contact.state.in_(['GA','IL','IA','LA','NV','NJ','PA','PR','VA','WI','WY'])
                    ), 'Match'),
                    # Missing company name
                    (Company.name.is_(null()), 'Missing Value'),
                    # Default case
                    else_='Mismatch'
                ).label('state_check')
            )
            .select_from(Contact)
            .outerjoin(Company, and_(
                Company.id == Contact.company_id,
                Company.company_type.in_([2, 7])
            ))
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Address validation filters from environment variables
                    Contact.acctid == self.address_acctid,
                    Contact.c_type == self.address_c_type,
                    Contact.del_ == False,  # Exclude deleted clients
                    Contact.iscoapp == self.address_iscoapp,  # Exclude co-app
                    Contact.leadstatus == self.address_leadstatus  # Include just leads with Submitted status
                )
            )
        )
        
        result = await self.session.execute(stmt, {"contact_id": contact_id})
        row = result.fetchone()
        
        if row:
            # Determine the result based on state_check only (since we only have state_check now)
            address_validation_result = self._determine_address_result_simple(row.state_check)
            
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "state": row.state,
                "assigned_company": row.assigned_company,
                "state_check": row.state_check,
                "address_validation_result": address_validation_result,
            }
        return None
    
    def _determine_address_result_simple(self, state_check: str) -> str:
        """Determine the address validation result based on state check only."""
        if state_check == 'Match':
            return 'pass'
        elif state_check == 'Mismatch':
            return 'no_pass'
        elif state_check == 'Missing Value':
            return 'no_data'
        else:
            return 'unknown'
    
    async def check_contact_eligibility(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Check if a contact is eligible for validation process with detailed reasons."""
        masked_id = mask_contact_id(contact_id)
        logger.debug(f"Executing eligibility check query for contact {masked_id}")
        
        # First, get the basic contact information
        basic_stmt = (
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
        
        result = await self.session.execute(basic_stmt, {"contact_id": contact_id})
        row = result.fetchone()
        
        if not row:
            logger.debug(f"Contact {masked_id} not found in database")
            return {
                "contact_id": contact_id,
                "eligible": False,
                "reason": "Contact not found in database"
            }
        
        # Check each eligibility condition individually
        reasons = []
        
        # Check account ID (must not be 5783)
        if row.acctid == 5783:
            reasons.append("Contact is in company type 5783 (excluded from validation)")
        
        # Check contact category (must be 'Underwriting')
        if row.contact_category != 'Underwriting':
            reasons.append(f"Contact is not in underwriting stage (current stage: {row.contact_category})")
        
        # Check if contact is deleted
        if row.del_ == True:
            reasons.append("Contact is marked as deleted")
        
        # Check if contact is co-applicant
        if row.iscoapp == 1:
            reasons.append("Contact is a co-applicant (excluded from validation)")
        
        # Check lead status (must be 'Submitted')
        if row.contact_lead_status != 'Submitted':
            reasons.append(f"Contact is not in submitted status (current status: {row.contact_lead_status})")
        
        # If all checks pass, contact is eligible
        if not reasons:
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
        
        # Contact is not eligible
        reason_text = "; ".join(reasons)
        logger.debug(f"Contact {masked_id} eligibility check failed: {reason_text}")
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
            "reason": reason_text
        } 
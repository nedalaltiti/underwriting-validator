"""
Contract Email Repository for email validation data operations.

This repository handles email validation queries for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, bindparam, and_, or_, null
from underwriting_validation.db.models import Contact, ContactFile
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContractEmailRepository:
    """Repository for contract email validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contract_email_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch email data for contract validation."""
        from underwriting_validation.db.models import FinancialAnalysis
        
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.email.label('forth_email'),
                FinancialAnalysis.applicant_email.label('contract_email')
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(FinancialAnalysis, FinancialAnalysis.file_id == ContactFile.id)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    )
                )
            )
        )
        
        result = await self.session.execute(stmt, {"contact_id": contact_id})
        row = result.fetchone()
        
        if row and (row.forth_email or row.contract_email):
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "forth_email": row.forth_email,
                "contract_email": row.contract_email
            }
        return None

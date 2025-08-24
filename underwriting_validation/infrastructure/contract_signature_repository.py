"""
Contract Signature Repository for signature validation data operations.

This repository handles signature validation queries for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, bindparam, and_, or_, null
from underwriting_validation.db.models import Contact, ContactFile
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContractSignatureRepository:
    """Repository for contract signature validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contract_signature_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch signature data for contract validation."""
        from underwriting_validation.db.models import EngagementTerm
        
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                EngagementTerm.client_signature,
                EngagementTerm.client_signature_date,
                EngagementTerm.coclient_signature,
                EngagementTerm.coclient_signature_date
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(EngagementTerm, EngagementTerm.file_id == ContactFile.id)
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
        
        if row and (row.client_signature or row.coclient_signature):
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "client_signature": row.client_signature,
                "client_signature_date": row.client_signature_date,
                "coclient_signature": row.coclient_signature,
                "coclient_signature_date": row.coclient_signature_date
            }
        return None

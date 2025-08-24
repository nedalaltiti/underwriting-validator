"""
Contract IP Repository for IP address validation data operations.

This repository handles IP address validation queries for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, bindparam, and_, or_, null
from underwriting_validation.db.models import Contact, ContactFile
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContractIPRepository:
    """Repository for contract IP address validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contract_ip_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch IP address data for contract validation."""
        from underwriting_validation.db.models import ClixsignCertificateSender, ClixsignCertificateSigner
        
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                ClixsignCertificateSender.sender_ip_address,
                ClixsignCertificateSigner.signer_ip_address
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(ClixsignCertificateSender, ClixsignCertificateSender.file_id == ContactFile.id)
            .outerjoin(ClixsignCertificateSigner, ClixsignCertificateSigner.file_id == ContactFile.id)
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
        
        if row and (row.sender_ip_address or row.signer_ip_address):
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "sender_ip_address": row.sender_ip_address,
                "signer_ip_address": row.signer_ip_address
            }
        return None

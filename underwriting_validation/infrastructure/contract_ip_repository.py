"""
Contract IP Repository for IP address validation data operations.

This repository handles IP address validation queries for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, bindparam, and_, or_, null
from underwriting_validation.db.models import Contact, ContactFile
from underwriting_validation.infrastructure.base.repository_base import ContractRepositoryBase

class ContractIPRepository(ContractRepositoryBase):
    """Repository for contract IP address validation database operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, "ContractIPRepository")
    
    def get_repository_type(self) -> str:
        """Return the repository type name."""
        return "contract_ip"
    
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
            .where(self.create_base_contact_filter(contact_id))
        )
        
        # Use base class method for standardized execution
        result_data = await self.execute_single_result_query(
            stmt, 
            contact_id, 
            "contract IP data fetch"
        )
        
        if result_data and (result_data.get('sender_ip_address') or result_data.get('signer_ip_address')):
            return {
                "contact_id": result_data['id'],
                "acctid": result_data['acctid'],
                "sender_ip_address": result_data['sender_ip_address'],
                "signer_ip_address": result_data['signer_ip_address']
            }
        return None

"""
FIX: contract_repository.py - Remove Session Storage

This shows how to fix the contract repository to prevent session leaks.
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging

logger = logging.getLogger(__name__)

# ❌ ORIGINAL BROKEN VERSION (for reference)
class BrokenContractRepository:
    def __init__(self, session: AsyncSession):
        self.session = session  # ❌ MEMORY LEAK: Session stored as instance variable
        
        # ❌ MEMORY LEAK: Multiple repositories sharing same session reference
        self.ip_repo = ContractIPRepository(session)
        self.email_repo = ContractEmailRepository(session)
        self.signature_repo = ContractSignatureRepository(session)
        # ... 9 more repositories - all holding session references

# ✅ FIXED VERSION
class FixedContractRepository:
    """Fixed contract repository without session storage."""
    
    def __init__(self):
        """Initialize repository without session storage."""
        # ✅ No session stored - prevents memory leaks
        self.repository_name = "ContractRepository"
        self.logger = logging.getLogger(__name__)
    
    async def fetch_contact_with_contract_data(
        self, 
        session: AsyncSession,  # ✅ Session passed as parameter
        contact_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch contact with contract validation data using provided session."""
        
        try:
            # ✅ Execute all queries concurrently with the same session
            # This fixes both the N+1 problem AND session management
            
            results = await asyncio.gather(
                self._fetch_ip_data(session, contact_id),
                self._fetch_email_data(session, contact_id),
                self._fetch_signature_data(session, contact_id),
                self._fetch_bank_data(session, contact_id),
                self._fetch_vlp_data(session, contact_id),
                self._fetch_gateway_data(session, contact_id),
                self._fetch_ssn_data(session, contact_id),
                self._fetch_dob_data(session, contact_id),
                self._fetch_debts_data(session, contact_id),
                return_exceptions=True  # ✅ Don't fail entire operation if one query fails
            )
            
            # ✅ Process results safely
            (ip_data, email_data, signature_data, bank_data, vlp_data, 
             gateway_data, ssn_data, dob_data, debts_data) = results
            
            # ✅ Check if any data was found
            data_found = any(
                result and not isinstance(result, Exception) 
                for result in results
            )
            
            if data_found:
                return {
                    "contact_id": contact_id,
                    "acctid": self._extract_acctid(results),
                    
                    # ✅ Safely extract data, handling exceptions
                    "sender_ip_address": self._safe_get(ip_data, 'sender_ip_address'),
                    "signer_ip_address": self._safe_get(ip_data, 'signer_ip_address'),
                    
                    "forth_email": self._safe_get(email_data, 'forth_email'),
                    "contract_email": self._safe_get(email_data, 'contract_email'),
                    
                    "client_signature": self._safe_get(signature_data, 'client_signature'),
                    "coclient_signature": self._safe_get(signature_data, 'coclient_signature'),
                    
                    # ... other data fields
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching contract data for contact {contact_id}: {e}")
            raise
    
    def _safe_get(self, data_result, key: str):
        """Safely extract value from result, handling exceptions."""
        if isinstance(data_result, Exception):
            return None
        return data_result.get(key) if data_result else None
    
    def _extract_acctid(self, results):
        """Extract acctid from first valid result."""
        for result in results:
            if not isinstance(result, Exception) and result:
                acctid = result.get('acctid')
                if acctid:
                    return acctid
        return None
    
    async def _fetch_ip_data(self, session: AsyncSession, contact_id: int):
        """Fetch IP data using provided session."""
        from underwriting_validation.db.models import Contact, ContactFile, ClixsignCertificateSender, ClixsignCertificateSigner
        from sqlalchemy import select, and_, or_, null, bindparam
        
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
                    or_(Contact.del_.is_(null()), Contact.del_ != True)
                )
            )
        )
        
        result = await session.execute(stmt, {"contact_id": contact_id})
        row = result.fetchone()
        
        if row and (row.sender_ip_address or row.signer_ip_address):
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "sender_ip_address": row.sender_ip_address,
                "signer_ip_address": row.signer_ip_address
            }
        return None
    
    # ✅ Similar pattern for other fetch methods
    async def _fetch_email_data(self, session: AsyncSession, contact_id: int):
        """Fetch email data using provided session."""
        # Implementation similar to _fetch_ip_data
        # Uses session parameter, no session storage
        pass
    
    async def _fetch_signature_data(self, session: AsyncSession, contact_id: int):
        """Fetch signature data using provided session."""
        pass
    
    async def _fetch_bank_data(self, session: AsyncSession, contact_id: int):
        """Fetch bank data using provided session."""
        pass
    
    async def _fetch_vlp_data(self, session: AsyncSession, contact_id: int):
        """Fetch VLP data using provided session."""
        pass
    
    async def _fetch_gateway_data(self, session: AsyncSession, contact_id: int):
        """Fetch gateway data using provided session."""
        pass
    
    async def _fetch_ssn_data(self, session: AsyncSession, contact_id: int):
        """Fetch SSN data using provided session."""
        pass
    
    async def _fetch_dob_data(self, session: AsyncSession, contact_id: int):
        """Fetch DOB data using provided session."""
        pass
    
    async def _fetch_debts_data(self, session: AsyncSession, contact_id: int):
        """Fetch debts data using provided session."""
        pass


# ✅ USAGE EXAMPLE: How to use the fixed repository
async def example_usage():
    """Example of how to use the fixed repository properly."""
    
    from underwriting_validation.db.session import get_db_session_context
    
    # ✅ Session scope limited to this operation
    async with get_db_session_context() as session:
        # ✅ Repository doesn't store session
        repo = FixedContractRepository()
        
        # ✅ Session passed as parameter
        result = await repo.fetch_contact_with_contract_data(session, 12345)
        
        # ✅ Session automatically closed when context exits
        return result
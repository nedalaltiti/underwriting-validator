"""
Contract Bank Repository for bank validation data operations.

This repository handles bank validation queries for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, bindparam, and_, or_, null
from underwriting_validation.db.models import Contact, ContactFile, PaymentGatewayBankInfo, BankAccount
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContractBankRepository:
    """Repository for contract bank validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contract_bank_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch bank data for contract validation."""
        # First, get contract bank data
        contract_bank_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentGatewayBankInfo.account_number,
                PaymentGatewayBankInfo.routing_number,
                PaymentGatewayBankInfo.bank_name,
                PaymentGatewayBankInfo.account_type,
                PaymentGatewayBankInfo.address
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(PaymentGatewayBankInfo, PaymentGatewayBankInfo.file_id == ContactFile.id)
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
        
        # Get Forth bank data
        forth_bank_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                BankAccount.account_num,
                BankAccount.routing_num,
                BankAccount.bank_name,
                BankAccount.account_type,
                BankAccount.bank_address
            )
            .select_from(Contact)
            .outerjoin(BankAccount, BankAccount.contact_id == Contact.id)
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
        
        # Execute both queries
        contract_result = await self.session.execute(contract_bank_stmt, {"contact_id": contact_id})
        forth_result = await self.session.execute(forth_bank_stmt, {"contact_id": contact_id})
        
        contract_row = contract_result.fetchone()
        forth_row = forth_result.fetchone()
        
        # Check if we have any bank data
        has_contract_bank_data = contract_row and any([
            contract_row.account_number,
            contract_row.routing_number,
            contract_row.bank_name,
            contract_row.account_type,
            contract_row.address
        ])
        
        has_forth_bank_data = forth_row and any([
            forth_row.account_num,
            forth_row.routing_num,
            forth_row.bank_name,
            forth_row.account_type,
            forth_row.bank_address
        ])
        
        if has_contract_bank_data or has_forth_bank_data:
            # Normalize account type for Forth data
            forth_account_type = None
            if forth_row and forth_row.account_type:
                if forth_row.account_type == '1':
                    forth_account_type = 'checking'
                elif forth_row.account_type == '2':
                    forth_account_type = 'savings'
                else:
                    forth_account_type = forth_row.account_type
            
            return {
                "contact_id": contact_id,
                "acctid": (contract_row or forth_row).acctid if (contract_row or forth_row) else None,
                # Contract bank data
                "contract_account_number": contract_row.account_number if contract_row else None,
                "contract_routing_number": contract_row.routing_number if contract_row else None,
                "contract_bank_name": contract_row.bank_name if contract_row else None,
                "contract_account_type": contract_row.account_type if contract_row else None,
                "contract_address": contract_row.address if contract_row else None,
                # Forth bank data
                "forth_account_number": forth_row.account_num if forth_row else None,
                "forth_routing_number": forth_row.routing_num if forth_row else None,
                "forth_bank_name": forth_row.bank_name if forth_row else None,
                "forth_account_type": forth_account_type,
                "forth_address": forth_row.bank_address if forth_row else None,
            }
        return None

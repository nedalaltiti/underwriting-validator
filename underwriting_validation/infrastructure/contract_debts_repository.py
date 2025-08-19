"""
Contract Debts Repository for debts validation data operations.

This repository handles debts validation queries for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, bindparam, and_, or_, null
from underwriting_validation.db.models import Contact, ContactFile, DebtSchedule, Debt
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContractDebtsRepository:
    """Repository for contract debts validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contract_debts_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch debts data for contract validation."""
        # First, get Forth debt count
        forth_debts_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                func.count(Debt.id).label('forth_debt_count')
            )
            .select_from(Contact)
            .outerjoin(Debt, and_(Debt.contact_id == Contact.id, Debt.enrolled == 1))
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
            .group_by(Contact.id, Contact.acctid)
        )
        
        # Get contract debt count
        contract_debts_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                func.count(DebtSchedule.id).label('contract_debt_count')
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(DebtSchedule, DebtSchedule.file_id == ContactFile.id)
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
            .group_by(Contact.id, Contact.acctid)
        )
        
        # Execute both queries
        forth_result = await self.session.execute(forth_debts_stmt, {"contact_id": contact_id})
        contract_result = await self.session.execute(contract_debts_stmt, {"contact_id": contact_id})
        
        forth_row = forth_result.fetchone()
        contract_row = contract_result.fetchone()
        
        if forth_row or contract_row:
            forth_debt_count = forth_row.forth_debt_count if forth_row else 0
            contract_debt_count = contract_row.contract_debt_count if contract_row else 0
            
            # Calculate debt count check
            debt_count_check = "Missing Value"
            if forth_debt_count > 0 or contract_debt_count > 0:
                if forth_debt_count == contract_debt_count:
                    debt_count_check = "Match"
                else:
                    debt_count_check = "Mismatch"
            
            return {
                "contact_id": contact_id,
                "acctid": (forth_row or contract_row).acctid if (forth_row or contract_row) else None,
                "forth_debt_count": forth_debt_count,
                "contract_debt_count": contract_debt_count,
                "debt_count_check": debt_count_check
            }
        return None

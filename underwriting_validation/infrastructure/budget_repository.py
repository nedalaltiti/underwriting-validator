"""
Budget Repository for budget-related data operations.

This repository handles budget data queries and calculations.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, bindparam, and_, or_, null
from underwriting_validation.db.models import Contact, BudgetData, BudgetFields
from underwriting_validation.config.settings import settings

logger = logging.getLogger(__name__)

class BudgetRepository:
    """Repository for budget-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Budget repository doesn't need base query settings since eligibility check handles base conditions
        pass
    
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
                    # Base conditions are already checked by eligibility check
                    Contact.id == bindparam('contact_id')
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

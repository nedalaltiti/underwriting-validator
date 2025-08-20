"""
Credit Score Repository for credit score validation data operations.

This repository handles credit score queries and calculations.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, bindparam, and_, or_, null, distinct
from underwriting_validation.db.models import Contact, CreditScores
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class CreditScoreRepository:
    """Repository for credit score validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contact_with_credit_score_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with credit score data using the provided SQL query."""
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                func.coalesce(CreditScores.equifax, 0).label('equifax'),
                func.coalesce(CreditScores.experian, 0).label('experian'),
                func.coalesce(CreditScores.transunion, 0).label('transunion'),
                (func.coalesce(CreditScores.equifax, 0) + 
                 func.coalesce(CreditScores.experian, 0) + 
                 func.coalesce(CreditScores.transunion, 0)).label('credit_score')
            )
            .select_from(Contact)
            .outerjoin(
                CreditScores, 
                and_(
                    CreditScores.contact_id == Contact.id,
                    CreditScores.id == select(func.max(CreditScores.id))
                    .where(CreditScores.contact_id == Contact.id)
                    .scalar_subquery()
                )
            )
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
        
        if row:
            # Determine if credit score data exists (check for valid scores > 0)
            has_credit_data = (row.equifax > 0 or row.experian > 0 or row.transunion > 0)
            total_credit_score = float(row.credit_score or 0)
            
            # Determine credit score status with enhanced handling for zero values
            if not has_credit_data or total_credit_score == 0:
                credit_score_status = "missing"
                if not has_credit_data:
                    credit_score_message = "Credit score data is missing or unavailable"
                else:
                    credit_score_message = "Credit score data exists but all values are zero or invalid"
            elif total_credit_score < 500:
                credit_score_status = "low"
                credit_score_message = f"Credit score is below 500 (Total: {total_credit_score})"
            else:
                credit_score_status = "acceptable"
                credit_score_message = f"Credit score is acceptable (Total: {total_credit_score})"
            
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "equifax": float(row.equifax or 0),
                "experian": float(row.experian or 0),
                "transunion": float(row.transunion or 0),
                "credit_score": total_credit_score,
                "has_credit_data": has_credit_data,
                "credit_score_status": credit_score_status,
                "credit_score_message": credit_score_message
            }
        return None

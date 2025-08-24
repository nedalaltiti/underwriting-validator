"""
Draft Repository for draft-related data operations.

This repository handles draft data queries and calculations for minimum payment validation.
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, bindparam, and_, or_, null, extract
from underwriting_validation.db.models import Contact, PaymentScheduleData
from underwriting_validation.config.settings import settings

logger = logging.getLogger(__name__)

class DraftRepository:
    """Repository for draft-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        pass
    
    async def fetch_contact_with_draft_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with draft data using a single query."""
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.del_,
                Contact.iscoapp,
                Contact.c_type,
                Contact.leadstatus,
                extract('YEAR', PaymentScheduleData.payment_date).label('pay_year'),
                extract('MONTH', PaymentScheduleData.payment_date).label('pay_month'),
                func.sum(PaymentScheduleData.fee1).label('total_payment'),
                func.count(PaymentScheduleData.id).label('payment_count')
            )
            .select_from(Contact)
            .outerjoin(PaymentScheduleData, Contact.id == PaymentScheduleData.contact_id)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter for contacts
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    ),
                    # Soft-delete filter for payment schedule data
                    or_(
                        PaymentScheduleData._fivetran_deleted.is_(null()),
                        PaymentScheduleData._fivetran_deleted != True
                    )
                )
            )
            .group_by(
                Contact.id, 
                Contact.acctid, 
                Contact.del_, 
                Contact.iscoapp, 
                Contact.c_type, 
                Contact.leadstatus,
                extract('YEAR', PaymentScheduleData.payment_date),
                extract('MONTH', PaymentScheduleData.payment_date)
            )
            .order_by(
                extract('YEAR', PaymentScheduleData.payment_date),
                extract('MONTH', PaymentScheduleData.payment_date)
            )
        )
        
        result = await self.session.execute(stmt, {"contact_id": contact_id})
        rows = result.fetchall()
        
        if not rows:
            return None
        
        # Process the results
        monthly_payments = []
        total_payments = 0
        payment_count = 0
        
        for row in rows:
            if row.pay_year and row.pay_month and row.total_payment:
                monthly_payment = {
                    "year": int(row.pay_year),
                    "month": int(row.pay_month),
                    "total_payment": float(row.total_payment),
                    "over_250": row.total_payment >= 250
                }
                monthly_payments.append(monthly_payment)
                total_payments += float(row.total_payment)
                payment_count += int(row.payment_count or 0)
        
        # Get contact info from first row
        first_row = rows[0]
        
        return {
            "contact_id": first_row.id,
            "acctid": first_row.acctid,
            "del_flag": first_row.del_,
            "iscoapp": first_row.iscoapp,
            "c_type": first_row.c_type,
            "leadstatus": first_row.leadstatus,
            "monthly_payments": monthly_payments,
            "total_payments": total_payments,
            "payment_count": payment_count,
            "months_with_data": len(monthly_payments)
        }

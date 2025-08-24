"""
Contract Gateway Repository for gateway validation data operations.

This repository handles gateway validation queries for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, bindparam, and_, or_, null, Integer
from underwriting_validation.db.models import Contact, ContactFile, PaymentGatewayAgreement, PaymentGatewayDepositSchedule, PaymentScheduleData
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContractGatewayRepository:
    """Repository for contract gateway validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contract_gateway_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch gateway data for contract validation."""
        # Gateway signature query
        signature_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentGatewayAgreement.client_signature
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(PaymentGatewayAgreement, PaymentGatewayAgreement.file_id == ContactFile.id)
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
        
        # Payment count query
        payment_count_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentGatewayAgreement.file_id,
                func.max(func.cast(PaymentGatewayDepositSchedule.payment_no, Integer)).label('contract_payment_count'),
                func.max(PaymentScheduleData.payment_num).label('forth_payment_count')
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(PaymentGatewayAgreement, PaymentGatewayAgreement.file_id == ContactFile.id)
            .outerjoin(PaymentGatewayDepositSchedule, PaymentGatewayDepositSchedule.file_id == ContactFile.id)
            .outerjoin(PaymentScheduleData, PaymentScheduleData.contact_id == Contact.id)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    ),
                    # Only include non-deleted payment schedule data
                    PaymentScheduleData._fivetran_deleted == False
                )
            )
            .group_by(Contact.id, Contact.acctid, PaymentGatewayAgreement.file_id)
        )
        
        # Payment amounts and dates query
        payment_details_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentGatewayAgreement.file_id,
                PaymentScheduleData.payment_num,
                PaymentGatewayDepositSchedule.amount.label('contract_amount'),
                PaymentScheduleData.fee1.label('forth_amount'),
                PaymentGatewayDepositSchedule.process_date.label('contract_date'),
                PaymentScheduleData.payment_date.label('forth_date')
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(PaymentGatewayAgreement, PaymentGatewayAgreement.file_id == ContactFile.id)
            .outerjoin(PaymentGatewayDepositSchedule, PaymentGatewayDepositSchedule.file_id == ContactFile.id)
            .outerjoin(
                PaymentScheduleData, 
                and_(
                    PaymentScheduleData.contact_id == Contact.id,
                    PaymentScheduleData.payment_num == func.cast(PaymentGatewayDepositSchedule.payment_no, Integer)
                )
            )
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    ),
                    # Only include non-deleted payment schedule data
                    PaymentScheduleData._fivetran_deleted == False
                )
            )
        )
        
        # Execute all queries
        signature_result = await self.session.execute(signature_stmt, {"contact_id": contact_id})
        payment_count_result = await self.session.execute(payment_count_stmt, {"contact_id": contact_id})
        payment_details_result = await self.session.execute(payment_details_stmt, {"contact_id": contact_id})
        
        signature_row = signature_result.fetchone()
        payment_count_row = payment_count_result.fetchone()
        payment_details_rows = payment_details_result.fetchall()
        
        # Check if we have any gateway data
        has_signature_data = signature_row and signature_row.client_signature
        has_payment_count_data = payment_count_row and (payment_count_row.contract_payment_count or payment_count_row.forth_payment_count)
        has_payment_details_data = len(payment_details_rows) > 0
        
        if has_signature_data or has_payment_count_data or has_payment_details_data:
            # Calculate payment count check
            count_check = "Missing Value"
            if payment_count_row and payment_count_row.contract_payment_count is not None and payment_count_row.forth_payment_count is not None:
                if payment_count_row.contract_payment_count == payment_count_row.forth_payment_count:
                    count_check = "Match"
                else:
                    count_check = "Mismatch"
            
            # Process payment details
            payment_details = []
            for row in payment_details_rows:
                amount_check = "Missing Value"
                if row.contract_amount is not None and row.forth_amount is not None:
                    if row.contract_amount == row.forth_amount:
                        amount_check = "Match"
                    else:
                        amount_check = "Mismatch"
                
                date_check = "Missing Value"
                if row.contract_date is not None and row.forth_date is not None:
                    if row.contract_date == row.forth_date:
                        date_check = "Match"
                    else:
                        date_check = "Mismatch"
                
                payment_details.append({
                    "payment_num": row.payment_num,
                    "contract_amount": row.contract_amount,
                    "forth_amount": row.forth_amount,
                    "amount_check": amount_check,
                    "amount_diff": abs((row.contract_amount or 0) - (row.forth_amount or 0)),
                    "contract_date": row.contract_date,
                    "forth_date": row.forth_date,
                    "date_check": date_check
                })
            
            return {
                "contact_id": contact_id,
                "acctid": (signature_row or payment_count_row).acctid if (signature_row or payment_count_row) else None,
                # Gateway signature data
                "gateway_client_signature": signature_row.client_signature if signature_row else None,
                # Payment count data
                "contract_payment_count": payment_count_row.contract_payment_count if payment_count_row else None,
                "forth_payment_count": payment_count_row.forth_payment_count if payment_count_row else None,
                "count_check": count_check,
                # Payment details data
                "payment_details": payment_details
            }
        return None

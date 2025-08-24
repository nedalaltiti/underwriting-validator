"""
Contract VLP Repository for VLP validation data operations.

This repository handles VLP (Voluntary Legal Plan) validation queries for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, bindparam, and_, or_, null
from underwriting_validation.db.models import Contact, ContactFile, LegalPlanAgreement, EnrollmentPlan, EnrollmentDefaults2, PaymentScheduleData
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContractVLPRepository:
    """Repository for contract VLP validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contract_vlp_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch VLP (Voluntary Legal Plan) data for contract validation."""
        # Main VLP agreement data query
        vlp_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.firstname,
                Contact.lastname,
                Contact.ssn.label('forth_ssn'),
                Contact.dob.label('forth_dob'),
                LegalPlanAgreement.legal_plan_provider,
                LegalPlanAgreement.client_signature,
                LegalPlanAgreement.signature_date,
                LegalPlanAgreement.member_name.label('contract_name'),
                LegalPlanAgreement.member_ssn.label('contract_ssn'),
                LegalPlanAgreement.member_dob.label('contract_dob')
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(LegalPlanAgreement, LegalPlanAgreement.file_id == ContactFile.id)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    ),
                    # Only include records with legal plan provider
                    LegalPlanAgreement.legal_plan_provider.isnot(None)
                )
            )
        )
        
        # Client snapshot fees query
        snapshot_fees_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                func.split_part(EnrollmentPlan.fee2, ',', 4).label('legal_setup_fee_snapshot'),
                func.split_part(EnrollmentPlan.fee3, ',', 4).label('legal_monthly_fee_snapshot')
            )
            .select_from(Contact)
            .outerjoin(EnrollmentPlan, EnrollmentPlan.contact_id == Contact.id)
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
        
        # Enrollment tab fees query
        enrollment_fees_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentScheduleData.payment_date,
                PaymentScheduleData.fee2.label('legal_setup_fee_enrollment'),
                PaymentScheduleData.fee3.label('legal_monthly_fee_enrollment')
            )
            .select_from(Contact)
            .outerjoin(PaymentScheduleData, PaymentScheduleData.contact_id == Contact.id)
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
        
        # Enrollment plan name query
        plan_name_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                EnrollmentDefaults2.title.label('plan_name')
            )
            .select_from(Contact)
            .outerjoin(EnrollmentPlan, EnrollmentPlan.contact_id == Contact.id)
            .outerjoin(EnrollmentDefaults2, EnrollmentDefaults2.id == EnrollmentPlan.plan_id)
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
        
        # Execute all queries
        vlp_result = await self.session.execute(vlp_stmt, {"contact_id": contact_id})
        snapshot_fees_result = await self.session.execute(snapshot_fees_stmt, {"contact_id": contact_id})
        enrollment_fees_result = await self.session.execute(enrollment_fees_stmt, {"contact_id": contact_id})
        plan_name_result = await self.session.execute(plan_name_stmt, {"contact_id": contact_id})
        
        vlp_row = vlp_result.fetchone()
        snapshot_fees_row = snapshot_fees_result.fetchone()
        enrollment_fees_row = enrollment_fees_result.fetchone()
        plan_name_row = plan_name_result.fetchone()
        
        # Check if we have any VLP data
        has_vlp_data = vlp_row and vlp_row.legal_plan_provider
        has_fees_data = (snapshot_fees_row and (snapshot_fees_row.legal_setup_fee_snapshot or snapshot_fees_row.legal_monthly_fee_snapshot)) or \
                       (enrollment_fees_row and (enrollment_fees_row.legal_setup_fee_enrollment or enrollment_fees_row.legal_monthly_fee_enrollment))
        has_plan_data = plan_name_row and plan_name_row.plan_name
        
        if has_vlp_data or has_fees_data or has_plan_data:
            # Build forth name from firstname and lastname
            forth_name = None
            if vlp_row and vlp_row.firstname and vlp_row.lastname:
                forth_name = f"{vlp_row.firstname} {vlp_row.lastname}".strip()
            elif vlp_row and vlp_row.firstname:
                forth_name = vlp_row.firstname
            elif vlp_row and vlp_row.lastname:
                forth_name = vlp_row.lastname
            
            return {
                "contact_id": contact_id,
                "acctid": (vlp_row or snapshot_fees_row or enrollment_fees_row or plan_name_row).acctid if (vlp_row or snapshot_fees_row or enrollment_fees_row or plan_name_row) else None,
                # VLP agreement data
                "legal_plan_provider": vlp_row.legal_plan_provider if vlp_row else None,
                "client_signature": vlp_row.client_signature if vlp_row else None,
                "signature_date": vlp_row.signature_date if vlp_row else None,
                "contract_name": vlp_row.contract_name if vlp_row else None,
                "forth_name": forth_name,
                "contract_ssn": vlp_row.contract_ssn if vlp_row else None,
                "forth_ssn": vlp_row.forth_ssn if vlp_row else None,
                "contract_dob": vlp_row.contract_dob if vlp_row else None,
                "forth_dob": vlp_row.forth_dob if vlp_row else None,
                # Client snapshot fees
                "legal_setup_fee_snapshot": snapshot_fees_row.legal_setup_fee_snapshot if snapshot_fees_row else None,
                "legal_monthly_fee_snapshot": snapshot_fees_row.legal_monthly_fee_snapshot if snapshot_fees_row else None,
                # Enrollment tab fees
                "legal_setup_fee_enrollment": enrollment_fees_row.legal_setup_fee_enrollment if enrollment_fees_row else None,
                "legal_monthly_fee_enrollment": enrollment_fees_row.legal_monthly_fee_enrollment if enrollment_fees_row else None,
                "payment_date": enrollment_fees_row.payment_date if enrollment_fees_row else None,
                # Enrollment plan name
                "plan_name": plan_name_row.plan_name if plan_name_row else None,
            }
        return None

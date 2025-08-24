"""
Contract SSN Repository for SSN validation data operations.

This repository handles SSN validation queries for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, bindparam, and_, or_, null, String
from underwriting_validation.db.models import Contact, ContactFile, PaymentGatewayAgreement, LegalPlanAgreement, PowerOfAttorney, CreditReport, Applicant
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContractSSNRepository:
    """Repository for contract SSN validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contract_ssn_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch SSN data for contract validation."""
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentGatewayAgreement.client_ssn.label('payment_gateway_agreement_client_ssn'),
                LegalPlanAgreement.member_ssn.label('legal_plan_agreement_client_ssn'),
                PowerOfAttorney.client_ssn.label('power_of_attorney_client_ssn'),
                Applicant.ssn.label('credit_report_ssn')
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(PaymentGatewayAgreement, PaymentGatewayAgreement.file_id == ContactFile.id)
            .outerjoin(LegalPlanAgreement, LegalPlanAgreement.file_id == ContactFile.id)
            .outerjoin(PowerOfAttorney, PowerOfAttorney.file_id == ContactFile.id)
            .outerjoin(CreditReport, func.regexp_replace(CreditReport.filename, '^.*/([0-9]+)-.*$', '\\1') == func.cast(Contact.id, String))
            .outerjoin(Applicant, Applicant.credit_report_id == CreditReport.id)
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
        
        if row and any([row.payment_gateway_agreement_client_ssn, row.legal_plan_agreement_client_ssn, 
                       row.power_of_attorney_client_ssn, row.credit_report_ssn]):
            # Calculate SSN check
            ssn_check = "Missing Value"
            if row.legal_plan_agreement_client_ssn and row.power_of_attorney_client_ssn and row.credit_report_ssn:
                if (row.legal_plan_agreement_client_ssn == row.power_of_attorney_client_ssn and 
                    row.legal_plan_agreement_client_ssn == row.credit_report_ssn and
                    row.payment_gateway_agreement_client_ssn and
                    row.legal_plan_agreement_client_ssn[-4:] == row.payment_gateway_agreement_client_ssn[-4:]):
                    ssn_check = "Match"
                else:
                    ssn_check = "Mismatch"
            
            return {
                "contact_id": contact_id,
                "acctid": row.acctid,
                "payment_gateway_agreement_client_ssn": row.payment_gateway_agreement_client_ssn,
                "legal_plan_agreement_client_ssn": row.legal_plan_agreement_client_ssn,
                "power_of_attorney_client_ssn": row.power_of_attorney_client_ssn,
                "credit_report_ssn": row.credit_report_ssn,
                "ssn_check": ssn_check
            }
        return None

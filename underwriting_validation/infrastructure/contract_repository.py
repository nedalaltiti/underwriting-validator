"""
Contract Repository for contract validation data operations.

This repository orchestrates data access by delegating to specialized contract repositories.
It provides a unified interface for contract-related operations while maintaining
separation of concerns.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from underwriting_validation.infrastructure.contract_ip_repository import ContractIPRepository
from underwriting_validation.infrastructure.contract_email_repository import ContractEmailRepository
from underwriting_validation.infrastructure.contract_signature_repository import ContractSignatureRepository
from underwriting_validation.infrastructure.contract_bank_repository import ContractBankRepository
from underwriting_validation.infrastructure.contract_vlp_repository import ContractVLPRepository
from underwriting_validation.infrastructure.contract_gateway_repository import ContractGatewayRepository
from underwriting_validation.infrastructure.contract_ssn_repository import ContractSSNRepository
from underwriting_validation.infrastructure.contract_dob_repository import ContractDOBRepository
from underwriting_validation.infrastructure.contract_debts_repository import ContractDebtsRepository

logger = logging.getLogger(__name__)

class ContractRepository:
    """Orchestrating repository for contract validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Initialize specialized repositories
        self.ip_repo = ContractIPRepository(session)
        self.email_repo = ContractEmailRepository(session)
        self.signature_repo = ContractSignatureRepository(session)
        self.bank_repo = ContractBankRepository(session)
        self.vlp_repo = ContractVLPRepository(session)
        self.gateway_repo = ContractGatewayRepository(session)
        self.ssn_repo = ContractSSNRepository(session)
        self.dob_repo = ContractDOBRepository(session)
        self.debts_repo = ContractDebtsRepository(session)
        
        logger.info("ContractRepository initialized with specialized repositories")
    
    async def fetch_contact_with_contract_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with contract validation data using sequential queries for now."""
        # Fetch data from all specialized repositories sequentially to avoid connection pool issues
        try:
            ip_data = await self.ip_repo.fetch_contract_ip_data(contact_id)
        except Exception as e:
            logger.error(f"IP data fetch failed for contact {contact_id}: {e}")
            ip_data = None
            
        try:
            email_data = await self.email_repo.fetch_contract_email_data(contact_id)
        except Exception as e:
            logger.error(f"Email data fetch failed for contact {contact_id}: {e}")
            email_data = None
            
        try:
            signature_data = await self.signature_repo.fetch_contract_signature_data(contact_id)
        except Exception as e:
            logger.error(f"Signature data fetch failed for contact {contact_id}: {e}")
            signature_data = None
            
        try:
            bank_data = await self.bank_repo.fetch_contract_bank_data(contact_id)
        except Exception as e:
            logger.error(f"Bank data fetch failed for contact {contact_id}: {e}")
            bank_data = None
            
        try:
            vlp_data = await self.vlp_repo.fetch_contract_vlp_data(contact_id)
        except Exception as e:
            logger.error(f"VLP data fetch failed for contact {contact_id}: {e}")
            vlp_data = None
            
        try:
            gateway_data = await self.gateway_repo.fetch_contract_gateway_data(contact_id)
        except Exception as e:
            logger.error(f"Gateway data fetch failed for contact {contact_id}: {e}")
            gateway_data = None
            
        try:
            ssn_data = await self.ssn_repo.fetch_contract_ssn_data(contact_id)
        except Exception as e:
            logger.error(f"SSN data fetch failed for contact {contact_id}: {e}")
            ssn_data = None
            
        try:
            dob_data = await self.dob_repo.fetch_contract_dob_data(contact_id)
        except Exception as e:
            logger.error(f"DOB data fetch failed for contact {contact_id}: {e}")
            dob_data = None
            
        try:
            debts_data = await self.debts_repo.fetch_contract_debts_data(contact_id)
        except Exception as e:
            logger.error(f"Debts data fetch failed for contact {contact_id}: {e}")
            debts_data = None
        
        # Combine all data
        if ip_data or email_data or signature_data or bank_data or vlp_data or gateway_data or ssn_data or dob_data or debts_data:
            combined_data = {
                "contact_id": contact_id,
                "acctid": (ip_data or email_data or signature_data or bank_data).get('acctid') if (ip_data or email_data or signature_data or bank_data) else None,
                # IP data
                "sender_ip_address": ip_data.get('sender_ip_address') if ip_data else None,
                "signer_ip_address": ip_data.get('signer_ip_address') if ip_data else None,
                # Email data
                "forth_email": email_data.get('forth_email') if email_data else None,
                "contract_email": email_data.get('contract_email') if email_data else None,
                # Signature data
                "client_signature": signature_data.get('client_signature') if signature_data else None,
                "client_signature_date": signature_data.get('client_signature_date') if signature_data else None,
                "coclient_signature": signature_data.get('coclient_signature') if signature_data else None,
                "coclient_signature_date": signature_data.get('coclient_signature_date') if signature_data else None,
                # Bank data
                "contract_account_number": bank_data.get('contract_account_number') if bank_data else None,
                "forth_account_number": bank_data.get('forth_account_number') if bank_data else None,
                "contract_routing_number": bank_data.get('contract_routing_number') if bank_data else None,
                "forth_routing_number": bank_data.get('forth_routing_number') if bank_data else None,
                "contract_bank_name": bank_data.get('contract_bank_name') if bank_data else None,
                "forth_bank_name": bank_data.get('forth_bank_name') if bank_data else None,
                "contract_account_type": bank_data.get('contract_account_type') if bank_data else None,
                "forth_account_type": bank_data.get('forth_account_type') if bank_data else None,
                "contract_address": bank_data.get('contract_address') if bank_data else None,
                "forth_address": bank_data.get('forth_address') if bank_data else None,
                # VLP data
                "legal_plan_provider": vlp_data.get('legal_plan_provider') if vlp_data else None,
                "client_signature": vlp_data.get('client_signature') if vlp_data else None,
                "signature_date": vlp_data.get('signature_date') if vlp_data else None,
                "contract_name": vlp_data.get('contract_name') if vlp_data else None,
                "forth_name": vlp_data.get('forth_name') if vlp_data else None,
                "contract_ssn": vlp_data.get('contract_ssn') if vlp_data else None,
                "forth_ssn": vlp_data.get('forth_ssn') if vlp_data else None,
                "contract_dob": vlp_data.get('contract_dob') if vlp_data else None,
                "forth_dob": vlp_data.get('forth_dob') if vlp_data else None,
                "legal_setup_fee_snapshot": vlp_data.get('legal_setup_fee_snapshot') if vlp_data else None,
                "legal_monthly_fee_snapshot": vlp_data.get('legal_monthly_fee_snapshot') if vlp_data else None,
                "legal_setup_fee_enrollment": vlp_data.get('legal_setup_fee_enrollment') if vlp_data else None,
                "legal_monthly_fee_enrollment": vlp_data.get('legal_monthly_fee_enrollment') if vlp_data else None,
                "payment_date": vlp_data.get('payment_date') if vlp_data else None,
                "plan_name": vlp_data.get('plan_name') if vlp_data else None,
                # Gateway data
                "gateway_client_signature": gateway_data.get('gateway_client_signature') if gateway_data else None,
                "contract_payment_count": gateway_data.get('contract_payment_count') if gateway_data else None,
                "forth_payment_count": gateway_data.get('forth_payment_count') if gateway_data else None,
                "count_check": gateway_data.get('count_check') if gateway_data else None,
                "payment_details": gateway_data.get('payment_details') if gateway_data else None,
                # SSN data
                "payment_gateway_agreement_client_ssn": ssn_data.get('payment_gateway_agreement_client_ssn') if ssn_data else None,
                "legal_plan_agreement_client_ssn": ssn_data.get('legal_plan_agreement_client_ssn') if ssn_data else None,
                "power_of_attorney_client_ssn": ssn_data.get('power_of_attorney_client_ssn') if ssn_data else None,
                "credit_report_ssn": ssn_data.get('credit_report_ssn') if ssn_data else None,
                "ssn_check": ssn_data.get('ssn_check') if ssn_data else None,
                # DOB data
                "forth_dob": dob_data.get('forth_dob') if dob_data else None,
                "contract_dob": dob_data.get('contract_dob') if dob_data else None,
                "dob_check": dob_data.get('dob_check') if dob_data else None,
                "age_plus_18_check": dob_data.get('age_plus_18_check') if dob_data else None,
                # Debts data
                "forth_debt_count": debts_data.get('forth_debt_count') if debts_data else None,
                "contract_debt_count": debts_data.get('contract_debt_count') if debts_data else None,
                "debt_count_check": debts_data.get('debt_count_check') if debts_data else None,
            }
            
            return combined_data
        
        return None

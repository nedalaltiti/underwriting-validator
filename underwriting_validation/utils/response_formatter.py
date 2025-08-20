"""
Response Formatter for Combined Validation Service

This module handles formatting validation results into structured responses.
"""

import logging
from typing import Dict, Any, Optional
from underwriting_validation.utils.validation_responses import format_combined_validation_response

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """Handles formatting validation results into structured responses."""
    
    def __init__(self):
        pass
    
    def format_hardship_data(
        self, 
        hardship_data: Optional[Dict[str, Any]], 
        hardship_analysis: Optional[Any]
    ) -> Optional[Dict[str, Any]]:
        """Format hardship data with validation outcome."""
        if not hardship_data:
            return None
            
        return {
            "financial_hardship": hardship_data.get('financial_hardship', ''),
            "hardship_description": hardship_data.get('hardship_description', ''),
            "hardship_validation_analysis": hardship_analysis.reason if hardship_analysis else None,
            "hardship_confidence": hardship_analysis.confidence if hardship_analysis else None,
            "hardship_validation_result": hardship_analysis.result.value if hardship_analysis else None
        }
    
    def format_budget_data(
        self, 
        budget_data: Optional[Dict[str, Any]], 
        budget_analysis: Optional[Any]
    ) -> Optional[Dict[str, Any]]:
        """Format budget data with validation outcome."""
        if not budget_data:
            return None
            
        return {
            "total_net_income": budget_data.get('total_net_income', 0),
            "total_expenses": budget_data.get('total_expenses', 0),
            "budget_difference": budget_analysis.surplus if budget_analysis else None,
            "surplus_indication": budget_analysis.surplus_indication if budget_analysis else None,
            "budget_outcome": budget_analysis.result.value if budget_analysis else None
        }
    
    def format_address_data(
        self, 
        address_data: Optional[Dict[str, Any]], 
        address_analysis: Optional[Any]
    ) -> Optional[Dict[str, Any]]:
        """Format address data with validation outcome."""
        if not address_data:
            return None
            
        return {
            "state": address_data.get('state'),
            "assigned_company": address_data.get('assigned_company'),
            "state_check": address_data.get('state_check'),
            "address_validation_result": address_analysis.result.value if address_analysis else None
        }
    
    def format_contract_data(
        self, 
        contract_data: Optional[Dict[str, Any]], 
        contract_analysis: Optional[Any]
    ) -> Optional[Dict[str, Any]]:
        """Format contract data with validation outcome."""
        if not contract_data or not contract_analysis:
            return None
            
        return {
            # IP Address Validation
            "sender_ip_address": contract_data.get('sender_ip_address'),
            "signer_ip_address": contract_data.get('signer_ip_address'),
            "ip_address_validation": contract_analysis.ip_address_validation,
            
            # Email Validation
            "forth_email": contract_data.get('forth_email'),
            "contract_email": contract_data.get('contract_email'),
            "email_address_validation": contract_analysis.email_address_validation,
            
            # Signature Validation
            "client_signature": contract_data.get('client_signature'),
            "coclient_signature": contract_data.get('coclient_signature'),
            "signature_validation": contract_analysis.signature_validation,
            
            # Bank Account Validation
            "contract_account_number": contract_data.get('contract_account_number'),
            "forth_account_number": contract_data.get('forth_account_number'),
            "contract_routing_number": contract_data.get('contract_routing_number'),
            "forth_routing_number": contract_data.get('forth_routing_number'),
            "contract_bank_name": contract_data.get('contract_bank_name'),
            "forth_bank_name": contract_data.get('forth_bank_name'),
            "contract_account_type": contract_data.get('contract_account_type'),
            "forth_account_type": contract_data.get('forth_account_type'),
            "contract_address": contract_data.get('contract_address'),
            "forth_address": contract_data.get('forth_address'),
            "bank_account_validation": contract_analysis.bank_account_validation,
            
            # VLP (Voluntary Legal Plan) Validation
            "legal_plan_provider": contract_data.get('legal_plan_provider'),
            "vlp_client_signature": contract_data.get('vlp_client_signature'),
            "vlp_signature_date": contract_data.get('vlp_signature_date'),
            "contract_name": contract_data.get('contract_name'),
            "forth_name": contract_data.get('forth_name'),
            "vlp_name_validation": contract_analysis.vlp_name_validation,
            "contract_ssn": contract_data.get('contract_ssn'),
            "forth_ssn": contract_data.get('forth_ssn'),
            "legal_setup_fee_snapshot": contract_data.get('legal_setup_fee_snapshot'),
            "legal_monthly_fee_snapshot": contract_data.get('legal_monthly_fee_snapshot'),
            "legal_setup_fee_enrollment": contract_data.get('legal_setup_fee_enrollment'),
            "legal_monthly_fee_enrollment": contract_data.get('legal_monthly_fee_enrollment'),
            "vlp_fees_validation": contract_analysis.vlp_fees_validation,
            "payment_date": contract_data.get('payment_date'),
            "plan_name": contract_data.get('plan_name'),
            "vlp_validation": contract_analysis.vlp_validation,
            
            # SSN Validation
            "payment_gateway_agreement_client_ssn": contract_data.get('payment_gateway_agreement_client_ssn'),
            "legal_plan_agreement_client_ssn": contract_data.get('legal_plan_agreement_client_ssn'),
            "power_of_attorney_client_ssn": contract_data.get('power_of_attorney_client_ssn'),
            "credit_report_ssn": contract_data.get('credit_report_ssn'),
            "ssn_check": contract_data.get('ssn_check'),
            "ssn_validation": contract_analysis.ssn_validation,
            
            # DOB Validation
            "forth_dob": contract_data.get('forth_dob'),
            "contract_dob": contract_data.get('contract_dob'),
            "dob_check": contract_data.get('dob_check'),
            "age_plus_18_check": contract_data.get('age_plus_18_check'),
            "dob_validation": contract_analysis.dob_validation,
            
            # Debts Validation
            "forth_debt_count": contract_data.get('forth_debt_count'),
            "contract_debt_count": contract_data.get('contract_debt_count'),
            "debt_count_check": contract_data.get('debt_count_check'),
            "debts_validation": contract_analysis.debts_validation,
            
            # Overall contract validation
            "contract_validation_result": contract_analysis.result.value
        }
    
    def format_duplication_data(
        self, 
        duplication_data: Optional[Dict[str, Any]], 
        duplication_analysis: Optional[Any]
    ) -> Optional[Dict[str, Any]]:
        """Format duplication data with validation outcome."""
        if not duplication_data or not duplication_analysis:
            return None
            
        return {
            "ssn": duplication_data.get('ssn'),
            "phone": duplication_data.get('phone'),
            "has_duplicates": duplication_analysis.has_duplicates,
            "ssn_duplicate_count": duplication_analysis.ssn_duplicate_count,
            "phone_duplicate_count": duplication_analysis.phone_duplicate_count,
            "ssn_duplicates": duplication_analysis.ssn_duplicates,
            "phone_duplicates": duplication_analysis.phone_duplicates,
            "duplication_validation_result": duplication_analysis.result,
            "duplication_reason": duplication_analysis.reason
        }
    
    def format_combined_response(
        self, 
        contact_id: int, 
        hardship_data: Optional[Dict[str, Any]], 
        budget_data: Optional[Dict[str, Any]],
        address_data: Optional[Dict[str, Any]],
        contract_data: Optional[Dict[str, Any]],
        hardship_analysis, 
        budget_analysis, 
        address_analysis, 
        contract_analysis, 
        combined_result: str,
        duplication_analysis=None
    ) -> str:
        """Format combined validation response."""
        return format_combined_validation_response(
            contact_id, hardship_analysis, budget_analysis, address_analysis, contract_analysis, combined_result, contract_data, duplication_analysis
        )

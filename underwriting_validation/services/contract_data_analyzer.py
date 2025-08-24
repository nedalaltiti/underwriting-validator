"""
Contract Data Analyzer

This module contains logic for analyzing contract data availability and determining validation results.
"""

import logging
from typing import Dict, Any, List
from underwriting_validation.services.contract_models import ContractDataIn, ContractValidity

logger = logging.getLogger(__name__)


class ContractDataAnalyzer:
    """Analyzes contract data availability and determines validation results."""
    
    @staticmethod
    def has_data_available(contract_data: ContractDataIn) -> Dict[str, bool]:
        """
        Check what types of contract data are available.
        
        Args:
            contract_data: Contract data to analyze
            
        Returns:
            Dictionary indicating which data types are available
        """
        return {
            "ip_data": bool(contract_data.sender_ip_address or contract_data.signer_ip_address),
            "email_data": bool(contract_data.forth_email or contract_data.contract_email),
            "signature_data": bool(contract_data.client_signature or contract_data.coclient_signature),
            "bank_data": bool(
                contract_data.contract_account_number or
                contract_data.forth_account_number or
                contract_data.contract_routing_number or
                contract_data.forth_routing_number or
                contract_data.contract_bank_name or
                contract_data.forth_bank_name or
                contract_data.contract_account_type or
                contract_data.forth_account_type or
                contract_data.contract_address or
                contract_data.forth_address
            ),
            "vlp_data": bool(
                contract_data.legal_plan_provider or
                contract_data.contract_name or
                contract_data.forth_name or
                contract_data.contract_ssn or
                contract_data.forth_ssn or
                contract_data.contract_dob or
                contract_data.forth_dob or
                contract_data.legal_setup_fee_snapshot or
                contract_data.legal_monthly_fee_snapshot or
                contract_data.legal_setup_fee_enrollment or
                contract_data.legal_monthly_fee_enrollment or
                contract_data.plan_name
            ),
            "gateway_data": bool(
                contract_data.gateway_client_signature or
                contract_data.contract_payment_count or
                contract_data.forth_payment_count or
                contract_data.payment_details
            ),
            "ssn_data": bool(
                contract_data.payment_gateway_agreement_client_ssn or
                contract_data.legal_plan_agreement_client_ssn or
                contract_data.power_of_attorney_client_ssn or
                contract_data.credit_report_ssn
            ),
            "dob_data": bool(
                contract_data.forth_dob or
                contract_data.contract_dob
            ),
            "debts_data": bool(
                contract_data.forth_debt_count or
                contract_data.contract_debt_count
            )
        }
    
    @staticmethod
    def determine_overall_result(checks: List[str]) -> tuple[ContractValidity, str]:
        """
        Determine the overall contract validation result based on individual checks.
        
        Args:
            checks: List of validation check results
            
        Returns:
            Tuple of (result, reason)
        """
        valid_checks = [check for check in checks if check in ["Match", "Valid"]]
        missing_checks = [check for check in checks if check == "Missing Value"]
        invalid_checks = [check for check in checks if check in ["Mismatch", "Invalid"]]
        
        if len(valid_checks) == len(checks):
            return ContractValidity.PASS, "All contract validations passed"
        elif len(invalid_checks) > 0:
            return ContractValidity.NO_PASS, f"Contract validation failed: {', '.join(invalid_checks)}"
        elif len(missing_checks) == len(checks):
            return ContractValidity.NO_DATA, "No contract data available for validation"
        else:
            return ContractValidity.MIXED, f"Mixed contract validation results: {', '.join(checks)}"
    
    @staticmethod
    def has_any_data(contract_data: ContractDataIn) -> bool:
        """
        Check if any contract data is available at all.
        
        Args:
            contract_data: Contract data to check
            
        Returns:
            True if any data is available, False otherwise
        """
        data_availability = ContractDataAnalyzer.has_data_available(contract_data)
        return any(data_availability.values())

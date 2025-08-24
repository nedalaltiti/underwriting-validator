"""
Combined Validation Service for Underwriting

This service orchestrates combined hardship, budget, address, contract, and duplication validation analysis.
It provides a unified interface for analyzing all validation types for a given contact ID.
"""

import logging
from typing import Optional, Dict, Any
from underwriting_validation.services.hardship_validation_service import HardshipValidationService
from underwriting_validation.services.budget_validation_service import BudgetValidationService
from underwriting_validation.services.address_validation_service import AddressValidationService
from underwriting_validation.services.contract_validation_service import ContractValidationService
from underwriting_validation.services.duplication_validation_service import DuplicationValidationService
from underwriting_validation.services.draft_validation_service import DraftValidationService
from underwriting_validation.infrastructure.contact_repository import ContactRepository
from underwriting_validation.utils.validation_responses import format_error_response, format_no_data_response, format_combined_validation_response
from underwriting_validation.utils.combined_result_analyzer import CombinedResultAnalyzer
from underwriting_validation.utils.pii_filter import mask_contact_id
from underwriting_validation.utils.data_fetcher import DataFetcher
from underwriting_validation.utils.analysis_orchestrator import AnalysisOrchestrator
from underwriting_validation.utils.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)

class CombinedValidationService:
    """Service for performing combined validation analysis."""
    
    def __init__(
        self, 
        hardship_service: HardshipValidationService, 
        budget_service: BudgetValidationService, 
        address_service: AddressValidationService, 
        contract_service: ContractValidationService, 
        duplication_service: DuplicationValidationService, 
        draft_service: DraftValidationService,
        repository: ContactRepository
    ):
        self.repository = repository
        self.analyzer = CombinedResultAnalyzer()
        
        # Initialize specialized components
        self.data_fetcher = DataFetcher(repository)
        self.analysis_orchestrator = AnalysisOrchestrator(
            hardship_service, budget_service, address_service, contract_service, duplication_service, draft_service
        )
        self.response_formatter = ResponseFormatter()
        
        logger.info("CombinedValidationService initialized with modular components")
    
    async def perform_combined_validation(
        self, 
        contact_id: int, 
        hardship_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Perform combined validation analysis.
        
        Args:
            contact_id: The ID of the contact to analyze
            hardship_data: Optional pre-fetched hardship data to avoid duplicate queries
            
        Returns:
            Dictionary containing combined validation analysis results
        """
        try:
            # First check if contact is eligible for validation
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Checking eligibility for contact {masked_id}")
            eligibility_data = await self.repository.check_contact_eligibility(contact_id)
            if not eligibility_data or not eligibility_data.get('eligible', False):
                logger.warning(f"Contact {masked_id} is not eligible for validation")
                reason = eligibility_data.get('reason', 'Contact is not eligible for validation process') if eligibility_data else 'Contact not found'
                return self._create_eligibility_error_response(contact_id, reason, eligibility_data)
            
            logger.info(f"Contact {masked_id} is eligible for validation")
            
            # Fetch all data in parallel using the data fetcher
            hardship_data, budget_data, address_data, contract_data, duplication_data, draft_data = await self.data_fetcher.fetch_all_validation_data(
                contact_id, hardship_data
            )
            
            # Check data availability using the data fetcher
            data_availability = self.data_fetcher.check_data_availability(
                hardship_data, budget_data, address_data, contract_data, duplication_data, draft_data
            )
            
            # Check if we have any data at all
            if not any(data_availability.values()):
                logger.warning(f"No validation data found for contact {masked_id}")
                return self._create_no_data_response(contact_id, eligibility_data)
            
            # Run all LLM analyses in parallel using the analysis orchestrator
            hardship_analysis, budget_analysis, address_analysis, contract_analysis, duplication_analysis, draft_analysis = await self.analysis_orchestrator.run_parallel_analyses(
                contact_id, hardship_data, budget_data, address_data, contract_data, duplication_data, draft_data, data_availability
            )
            
            # Format all data using the response formatter
            formatted_hardship_data = self.response_formatter.format_hardship_data(hardship_data, hardship_analysis)
            formatted_budget_data = self.response_formatter.format_budget_data(budget_data, budget_analysis)
            formatted_address_data = self.response_formatter.format_address_data(address_data, address_analysis)
            formatted_draft_data = self.response_formatter.format_draft_data(draft_data, draft_analysis)
            
            # Build contract data with validation outcome using the new embedded pattern
            formatted_contract_data = None
            if contract_data and contract_analysis:
                formatted_contract_data = {
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
                    "vlp_plan_validation": contract_analysis.vlp_plan_validation,
                    
                    # Payment Gateway Validation
                    "gateway_client_signature": contract_data.get('gateway_client_signature'),
                    "gateway_signature_validation": contract_analysis.gateway_signature_validation,
                    "contract_payment_count": contract_data.get('contract_payment_count'),
                    "forth_payment_count": contract_data.get('forth_payment_count'),
                    "payment_count_validation": contract_analysis.payment_count_validation,
                    "payment_details": contract_data.get('payment_details'),
                    "payment_amounts_validation": contract_analysis.payment_amounts_validation,
                    "payment_dates_validation": contract_analysis.payment_dates_validation,
                    
                    # SSN Validation
                    "payment_gateway_agreement_client_ssn": contract_data.get('payment_gateway_agreement_client_ssn'),
                    "legal_plan_agreement_client_ssn": contract_data.get('legal_plan_agreement_client_ssn'),
                    "power_of_attorney_client_ssn": contract_data.get('power_of_attorney_client_ssn'),
                    "credit_report_ssn": contract_data.get('credit_report_ssn'),
                    "ssn_consistency_validation": contract_analysis.ssn_consistency_validation,
                    
                    # Date of Birth Validation
                    "forth_dob": contract_data.get('forth_dob'),
                    "contract_dob": contract_data.get('contract_dob'),
                    "dob_consistency_validation": contract_analysis.dob_consistency_validation,
                    "age_eligibility_validation": contract_analysis.age_eligibility_validation,
                    
                    # Debts Validation
                    "forth_debt_count": contract_data.get('forth_debt_count'),
                    "contract_debt_count": contract_data.get('contract_debt_count'),
                    "debt_count_validation": contract_analysis.debt_count_validation,
                    
                    # Overall Contract Validation Result
                    "contract_validation_result": contract_analysis.result.value if contract_analysis else None
                }
            
            # Build duplication data with validation outcome
            formatted_duplication_data = None
            if duplication_data and duplication_analysis:
                formatted_duplication_data = {
                    "ssn": duplication_data.get('ssn'),
                    "phone": duplication_data.get('phone'),
                    "has_duplicates": duplication_analysis.has_duplicates,
                    "ssn_duplicate_count": duplication_analysis.ssn_duplicate_count,
                    "phone_duplicate_count": duplication_analysis.phone_duplicate_count,
                    "ssn_duplicates": duplication_analysis.ssn_duplicates,
                    "phone_duplicates": duplication_analysis.phone_duplicates,
                    "duplication_validation_result": duplication_analysis.result if duplication_analysis else None,
                    "duplication_reason": duplication_analysis.reason
                }
            
            # Determine combined result and reason using the analyzer
            combined_result, combined_result_reason = self.analyzer.analyze_combined_result(
                hardship_analysis=formatted_hardship_data,
                budget_analysis=formatted_budget_data,
                address_analysis=formatted_address_data,
                contract_analysis=formatted_contract_data,
                duplication_analysis=formatted_duplication_data,
                draft_analysis=formatted_draft_data
            )
            logger.info(f"Combined validation result for contact {masked_id}: {combined_result} - {combined_result_reason}")
            
            # Format combined response
            formatted_response = self._format_combined_response(
                contact_id, hardship_data, budget_data, address_data, contract_data,
                hardship_analysis, budget_analysis, address_analysis, contract_analysis, combined_result, duplication_analysis, draft_analysis
            )
            
            return {
                "contact_id": contact_id,
                "eligibility": "eligible",
                "success": True,
                "combined_result": combined_result,
                "combined_result_reason": combined_result_reason,
                "message": formatted_response,
                "eligibility_data": eligibility_data,
                "hardship_data": formatted_hardship_data,
                "budget_data": formatted_budget_data,
                "address_data": formatted_address_data,
                "contract_data": formatted_contract_data,
                "duplication_data": formatted_duplication_data,
                "draft_data": formatted_draft_data,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error performing combined validation for contact {masked_id}: {e}")
            return {
                "contact_id": contact_id,
                "eligibility": "not eligible",
                "success": False,
                "combined_result": "error",
                "combined_result_reason": "Error occurred during validation analysis",
                "message": format_error_response(contact_id, f"Error analyzing validation data for contact {contact_id}. Please try again.", "validation"),
                "eligibility_data": None,
                "hardship_data": None,
                "budget_data": None,
                "address_data": None,
                "contract_data": None,
                "duplication_data": None,
                "draft_data": None,
                "error": str(e)
            }
    

    
    def _format_combined_response(
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
        duplication_analysis=None,
        draft_analysis=None
    ) -> str:
        """
        Format combined hardship, budget, address, contract, duplication, and draft analysis into a comprehensive response.
        """
        return format_combined_validation_response(
            contact_id, hardship_analysis, budget_analysis, address_analysis, contract_analysis, combined_result, contract_data, duplication_analysis, draft_analysis
        )
    
    async def validate_contact_with_prefetched_data(
        self, 
        contact_id: int, 
        hardship_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Optimized version that accepts pre-fetched hardship data.
        
        This method is specifically designed to avoid duplicate database queries when
        hardship data has already been fetched by other services.
        
        Args:
            contact_id: The ID of the contact to analyze
            hardship_data: Pre-fetched hardship data
            
        Returns:
            Dictionary containing combined validation analysis results
        """
        return await self.perform_combined_validation(contact_id, hardship_data)
    
    def _create_eligibility_error_response(
        self, 
        contact_id: int, 
        reason: str, 
        eligibility_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create error response for ineligible contacts."""
        return {
            "contact_id": contact_id,
            "eligibility": "not eligible",
            "success": False,
            "combined_result": "not_eligible",
            "combined_result_reason": reason,
            "message": f"Contact does not meet eligibility criteria: {reason}",
            "eligibility_data": eligibility_data,
            "hardship_data": None,
            "budget_data": None,
            "address_data": None,
            "contract_data": None,
            "duplication_data": None,
            "draft_data": None,
            "error": reason
        }
    
    def _create_no_data_response(
        self, 
        contact_id: int, 
        eligibility_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create response for contacts with no validation data."""
        return {
            "contact_id": contact_id,
            "eligibility": "eligible",
            "success": False,
            "combined_result": "no_data",
            "message": format_no_data_response(contact_id, "validation"),
            "eligibility_data": eligibility_data,
            "hardship_data": None,
            "budget_data": None,
            "address_data": None,
            "contract_data": None,
            "duplication_data": None,
            "draft_data": None,
            "error": "No contact data available"
        } 
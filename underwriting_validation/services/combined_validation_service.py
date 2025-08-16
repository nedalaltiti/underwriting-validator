"""
Combined Validation Service for Underwriting

This service handles combined hardship, budget, and address validation analysis.
It provides a unified interface for analyzing hardship, budget, and address data
for a given contact ID.
"""

import logging
from typing import Optional, Dict, Any
from underwriting_validation.services.hardship_validation_service import HardshipValidationService
from underwriting_validation.services.budget_validation_service import BudgetValidationService, BudgetDataIn
from underwriting_validation.services.address_validation_service import AddressValidationService, AddressDataIn
from underwriting_validation.infrastructure.contact_repository import ContactRepository
from underwriting_validation.utils.validation_responses import format_combined_validation_response, format_error_response, format_no_data_response
from underwriting_validation.utils.combined_result_analyzer import CombinedResultAnalyzer
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class CombinedValidationService:
    """Service for performing combined hardship, budget, and address validation analysis."""
    
    def __init__(self, hardship_service: HardshipValidationService, budget_service: BudgetValidationService, address_service: AddressValidationService, repository: ContactRepository):
        self.hardship_service = hardship_service
        self.budget_service = budget_service
        self.address_service = address_service
        self.repository = repository
        self.analyzer = CombinedResultAnalyzer()
        
        logger.info("CombinedValidationService initialized")
    
    async def perform_combined_validation(
        self, 
        contact_id: int, 
        hardship_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Perform combined hardship, budget, and address validation analysis.
        
        Args:
            contact_id: The ID of the contact to analyze
            hardship_data: Optional pre-fetched hardship data to avoid duplicate queries
            
        Returns:
            Dictionary containing combined hardship, budget, and address analysis results
        """
        try:
            # First check if contact is eligible for validation
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Checking eligibility for contact {masked_id}")
            eligibility_data = await self.repository.check_contact_eligibility(contact_id)
            if not eligibility_data:
                logger.warning(f"Contact {masked_id} is not eligible for validation")
                return {
                    "contact_id": contact_id,
                    "eligibility": "not eligible",
                    "success": False,
                    "combined_result": "not_eligible",
                    "combined_result_reason": "Contact is not eligible for validation process",
                    "message": "Contact does not meet eligibility criteria (category, status, or other requirements)",
                    "eligibility_data": None,
                    "hardship_data": None,
                    "budget_data": None,
                    "address_data": None,
                    "error": "Contact not eligible for validation"
                }
            
            logger.info(f"Contact {masked_id} is eligible for validation")
            
            # Use provided hardship data or fetch it
            if hardship_data is None:
                hardship_data = await self.repository.fetch_contact_with_hardship_data(contact_id)
            
            # Get budget data using repository
            budget_data = await self.repository.fetch_contact_with_budget_data(contact_id)
            
            # Get address data using repository
            address_data = await self.repository.fetch_contact_with_address_data(contact_id)
            
            # Check if we have any data at all
            has_hardship_data = hardship_data and any([
                hardship_data.get('financial_hardship'),
                hardship_data.get('hardship_description')
            ])
            
            has_budget_data = budget_data and any([
                budget_data.get('total_net_income', 0) > 0,
                budget_data.get('total_expenses', 0) > 0
            ])
            
            has_address_data = address_data and any([
                address_data.get('state'),
                address_data.get('assigned_company')
            ])
            
            if not has_hardship_data and not has_budget_data and not has_address_data:
                logger.warning(f"No hardship, budget, or address data found for contact {masked_id}")
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
                    "error": "No contact data available"
                }
            
            # Analyze hardship if data exists
            hardship_analysis = None
            hardship_validation_analysis = None
            hardship_validation_result = None
            hardship_confidence = None
            if has_hardship_data:
                hardship_result = await self.hardship_service.analyze_hardship_validity(hardship_data)
                if not hardship_result.is_error():
                    hardship_analysis = hardship_result.value
                    hardship_validation_analysis = hardship_analysis.reason
                    hardship_validation_result = hardship_analysis.result.value
                    hardship_confidence = hardship_analysis.confidence
                    logger.info(f"Hardship analysis for contact {masked_id}: result={hardship_validation_result}, confidence={hardship_confidence}")
                else:
                    logger.error(f"Hardship analysis failed for contact {masked_id}: {hardship_result.error}")
            
            # Analyze budget if data exists
            budget_analysis = None
            budget_difference = None
            budget_outcome = None
            budget_surplus_indication = None
            if has_budget_data:
                # Convert dictionary to Pydantic model for type safety
                budget_data_model = BudgetDataIn(
                    contact_id=budget_data['contact_id'],
                    total_net_income=budget_data['total_net_income'],
                    total_expenses=budget_data['total_expenses']
                )
                budget_result = await self.budget_service.analyze_budget_validity(budget_data_model)
                if not budget_result.is_error():
                    budget_analysis = budget_result.value
                    budget_difference = budget_analysis.surplus
                    budget_outcome = budget_analysis.result.value
                    budget_surplus_indication = budget_analysis.surplus_indication
                    logger.info(f"Budget analysis for contact {masked_id}: result={budget_outcome}, surplus={budget_surplus_indication}, difference=${budget_difference:,.2f}")
                else:
                    logger.error(f"Budget analysis failed for contact {masked_id}: {budget_result.error}")
            
            # Analyze address if data exists
            address_analysis = None
            address_validation_result = None
            if has_address_data:
                # Convert dictionary to Pydantic model for type safety
                address_data_model = AddressDataIn(
                    contact_id=address_data['contact_id'],
                    state=address_data.get('state'),
                    assigned_company=address_data.get('assigned_company')
                )
                address_result = await self.address_service.analyze_address_validity(address_data_model)
                if not address_result.is_error():
                    address_analysis = address_result.value
                    address_validation_result = address_analysis.result.value
                    logger.info(f"Address analysis for contact {masked_id}: result={address_validation_result}, state_check={address_analysis.state_check}")
                else:
                    logger.error(f"Address analysis failed for contact {masked_id}: {address_result.error}")
            
            # Build hardship data with validation outcome
            formatted_hardship_data = None
            if hardship_data:
                formatted_hardship_data = {
                    "financial_hardship": hardship_data.get('financial_hardship', ''),
                    "hardship_description": hardship_data.get('hardship_description', ''),
                    "hardship_validation_analysis": hardship_validation_analysis,
                    "hardship_confidence": hardship_confidence,
                    "hardship_validation_result": hardship_validation_result
                }
            
            # Build budget data with difference
            formatted_budget_data = None
            if budget_data:
                formatted_budget_data = {
                    "total_net_income": budget_data.get('total_net_income', 0),
                    "total_expenses": budget_data.get('total_expenses', 0),
                    "budget_difference": budget_difference,
                    "surplus_indication": budget_surplus_indication,
                    "budget_outcome": budget_outcome
                }
            
            # Build address data with validation outcome
            formatted_address_data = None
            if address_data:
                formatted_address_data = {
                    "state": address_data.get('state'),
                    "assigned_company": address_data.get('assigned_company'),
                    "state_check": address_data.get('state_check'),
                    "address_validation_result": address_validation_result
                }
            
            # Determine combined result and reason using the analyzer
            combined_result, combined_result_reason = self.analyzer.analyze_combined_result(
                hardship_analysis=formatted_hardship_data,
                budget_analysis=formatted_budget_data,
                address_analysis=formatted_address_data
            )
            logger.info(f"Combined validation result for contact {masked_id}: {combined_result} - {combined_result_reason}")
            
            # Format combined response
            formatted_response = self._format_combined_response(
                contact_id, hardship_data, budget_data, address_data, 
                hardship_analysis, budget_analysis, address_analysis, combined_result
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
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error performing combined validation for contact {masked_id}: {e}")
            return {
                "contact_id": contact_id,
                "eligibility": "not eligible",
                "success": False,
                "combined_result": "error",
                "message": format_error_response(contact_id, f"Error analyzing validation data for contact {contact_id}. Please try again.", "validation"),
                "eligibility_data": None,
                "hardship_data": None,
                "budget_data": None,
                "address_data": None,
                "error": str(e)
            }
    

    
    def _format_combined_response(
        self, 
        contact_id: int, 
        hardship_data: Dict[str, Any], 
        budget_data: Dict[str, Any],
        address_data: Dict[str, Any],
        hardship_analysis, 
        budget_analysis, 
        address_analysis, 
        combined_result: str
    ) -> str:
        """
        Format combined hardship, budget, and address analysis into a comprehensive response.
        """
        return format_combined_validation_response(
            contact_id, hardship_data, budget_data, address_data,
            hardship_analysis, budget_analysis, address_analysis, combined_result
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
            Dictionary containing combined hardship, budget, and address analysis results
        """
        return await self.perform_combined_validation(contact_id, hardship_data) 
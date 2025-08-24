"""
Contact Analysis Utilities

This module provides utilities for contact analysis operations including:
- Hardship analysis
- Budget analysis  
- Address analysis
- Analysis orchestration
"""

import logging
from typing import Optional, Dict, Any
from underwriting_validation.infrastructure.contact_repository import ContactRepository
from underwriting_validation.services.hardship_validation_service import HardshipValidationService
from underwriting_validation.services.budget_validation_service import BudgetValidationService, BudgetDataIn
from underwriting_validation.services.address_validation_service import AddressValidationService, AddressDataIn
from underwriting_validation.utils.pii_filter import mask_contact_id
from .contact_validation import validate_and_raise_if_invalid, ContactNotFoundError
from .contact_data import ContactDataCache, get_or_fetch_hardship_data, has_hardship_data, has_budget_data, has_address_data

logger = logging.getLogger(__name__)


async def analyze_contact_hardship(
    hardship_service: HardshipValidationService,
    repository: ContactRepository,
    cache: ContactDataCache,
    contact_id: int
) -> Optional[Dict[str, Any]]:
    """
    Retrieve hardship data and analyze its validity using the Gemini model.
    
    Args:
        hardship_service: Hardship validation service instance
        repository: Contact repository instance
        cache: Data cache instance
        contact_id: The ID of the contact to analyze
        
    Returns:
        Dictionary containing hardship analysis results or None if contact not found
    """
    validate_and_raise_if_invalid(contact_id)
    
    try:
        # Get hardship data using cached fetch
        hardship_data = await get_or_fetch_hardship_data(repository, cache, contact_id)
        
        masked_id = mask_contact_id(contact_id)
        if not hardship_data:
            logger.warning(f"Contact {masked_id} not found in database")
            raise ContactNotFoundError(f"Contact {contact_id} not found in database")
        
        # Check if there's any hardship data to analyze
        if not has_hardship_data(hardship_data):
            logger.info(f"No hardship data available for contact {masked_id}")
            from underwriting_validation.utils.validation_responses import format_no_data_response
            return {
                "contact_id": contact_id,
                "analysis": {
                    "result": "no_pass",
                    "confidence": 0.0,
                    "reason": "No hardship data available for analysis"
                },
                "formatted_response": format_no_data_response(contact_id, "hardship")
            }
        
        # Analyze hardship validity
        analysis_result = await hardship_service.analyze_hardship_validity(hardship_data)
        
        masked_id = mask_contact_id(contact_id)
        if analysis_result.is_error():
            logger.error(f"Hardship analysis failed for contact {masked_id}: {analysis_result.error}")
            from underwriting_validation.utils.validation_responses import format_error_response
            return {
                "contact_id": contact_id,
                "error": str(analysis_result.error),
                "analysis": None,
                "formatted_response": format_error_response(contact_id, f"Unable to analyze hardship data for contact {contact_id}. Please try again or contact support.", "hardship")
            }
        
        analysis = analysis_result.value
        formatted_response = hardship_service.format_hardship_response(analysis, hardship_data)
        
        return {
            "contact_id": contact_id,
            "hardship_data": hardship_data,
            "analysis": {
                "result": analysis.result.value,
                "confidence": analysis.confidence,
                "reason": analysis.reason
            },
            "formatted_response": formatted_response
        }
        
    except (ContactNotFoundError):
        # Re-raise these specific exceptions
        raise
    except Exception as e:
        masked_id = mask_contact_id(contact_id)
        logger.error(f"Error analyzing hardship for contact {masked_id}: {e}")
        from underwriting_validation.utils.validation_responses import format_error_response
        return {
            "contact_id": contact_id,
            "error": str(e),
            "analysis": None,
            "formatted_response": format_error_response(contact_id, f"Error analyzing hardship data for contact {contact_id}. Please try again.", "hardship")
        }


async def analyze_contact_budget(
    budget_service: BudgetValidationService,
    repository: ContactRepository,
    cache: ContactDataCache,
    contact_id: int
) -> Optional[Dict[str, Any]]:
    """
    Retrieve budget data and analyze if the client has a positive surplus.
    
    Args:
        budget_service: Budget validation service instance
        repository: Contact repository instance
        cache: Data cache instance
        contact_id: The ID of the contact to analyze
        
    Returns:
        Dictionary containing budget analysis results or None if contact not found
    """
    validate_and_raise_if_invalid(contact_id)
    
    try:
        # Get budget data
        budget_data = await repository.fetch_contact_with_budget_data(contact_id)
        
        masked_id = mask_contact_id(contact_id)
        if not budget_data:
            logger.warning(f"Contact {masked_id} not found in database")
            raise ContactNotFoundError(f"Contact {contact_id} not found in database")
        
        # Check if there's any budget data to analyze
        if not has_budget_data(budget_data):
            logger.info(f"No budget data available for contact {masked_id}")
            from underwriting_validation.utils.validation_responses import format_no_data_response
            return {
                "contact_id": contact_id,
                "analysis": {
                    "result": "no_pass",
                    "reason": "No budget data available for analysis"
                },
                "formatted_response": format_no_data_response(contact_id, "budget")
            }
        
        # Convert dictionary to Pydantic model for type safety
        budget_data_model = BudgetDataIn(
            contact_id=budget_data['contact_id'],
            total_net_income=budget_data['total_net_income'],
            total_expenses=budget_data['total_expenses']
        )
        
        # Analyze budget validity
        analysis_result = await budget_service.analyze_budget_validity(budget_data_model)
        
        masked_id = mask_contact_id(contact_id)
        if analysis_result.is_error():
            logger.error(f"Budget analysis failed for contact {masked_id}: {analysis_result.error}")
            from underwriting_validation.utils.validation_responses import format_error_response
            return {
                "contact_id": contact_id,
                "error": str(analysis_result.error),
                "analysis": None,
                "formatted_response": format_error_response(contact_id, f"Unable to analyze budget data for contact {contact_id}. Please try again or contact support.", "budget")
            }
        
        analysis = analysis_result.value
        formatted_response = budget_service.format_budget_response(analysis, budget_data_model)
        
        return {
            "contact_id": contact_id,
            "budget_data": budget_data,
            "analysis": {
                "surplus_indication": analysis.surplus_indication,
                "result": analysis.result.value,
                "reason": analysis.reason,
                "total_net_income": analysis.total_net_income,
                "total_expenses": analysis.total_expenses,
                "surplus": analysis.surplus
            },
            "formatted_response": formatted_response
        }
        
    except (ContactNotFoundError):
        # Re-raise these specific exceptions
        raise
    except Exception as e:
        masked_id = mask_contact_id(contact_id)
        logger.error(f"Error analyzing budget for contact {masked_id}: {e}")
        from underwriting_validation.utils.validation_responses import format_error_response
        return {
            "contact_id": contact_id,
            "error": str(e),
            "analysis": None,
            "formatted_response": format_error_response(contact_id, f"Error analyzing budget data for contact {contact_id}. {e}")
        }


async def analyze_contact_address(
    address_service: AddressValidationService,
    repository: ContactRepository,
    cache: ContactDataCache,
    contact_id: int
) -> Optional[Dict[str, Any]]:
    """
    Retrieve address data and analyze if the state/company assignment is valid.
    
    Args:
        address_service: Address validation service instance
        repository: Contact repository instance
        cache: Data cache instance
        contact_id: The ID of the contact to analyze
        
    Returns:
        Dictionary containing address analysis results or None if contact not found
    """
    validate_and_raise_if_invalid(contact_id)
    
    try:
        # Get address data
        address_data = await repository.fetch_contact_with_address_data(contact_id)
        
        masked_id = mask_contact_id(contact_id)
        if not address_data:
            logger.warning(f"Contact {masked_id} not found in database")
            raise ContactNotFoundError(f"Contact {contact_id} not found in database")
        
        # Check if there's any address data to analyze
        if not has_address_data(address_data):
            logger.info(f"No address data available for contact {masked_id}")
            from underwriting_validation.utils.validation_responses import format_no_data_response
            return {
                "contact_id": contact_id,
                "analysis": {
                    "result": "no_data",
                    "reason": "No address data available for analysis"
                },
                "formatted_response": format_no_data_response(contact_id, "address")
            }
        
        # Convert dictionary to Pydantic model for type safety
        address_data_model = AddressDataIn(
            contact_id=address_data['contact_id'],
            state=address_data.get('state'),
            assigned_company=address_data.get('assigned_company')
        )
        
        # Analyze address validity
        analysis_result = await address_service.analyze_address_validity(address_data_model)
        
        masked_id = mask_contact_id(contact_id)
        if analysis_result.is_error():
            logger.error(f"Address analysis failed for contact {masked_id}: {analysis_result.error}")
            from underwriting_validation.utils.validation_responses import format_error_response
            return {
                "contact_id": contact_id,
                "error": str(analysis_result.error),
                "analysis": None,
                "formatted_response": format_error_response(contact_id, f"Unable to analyze address data for contact {contact_id}. Please try again or contact support.", "address")
            }
        
        analysis = analysis_result.value
        formatted_response = address_service.format_address_response(analysis, address_data_model)
        
        return {
            "contact_id": contact_id,
            "address_data": address_data,
            "analysis": {
                "result": analysis.result.value,
                "reason": analysis.reason,
                "state_check": analysis.state_check
            },
            "formatted_response": formatted_response
        }
        
    except (ContactNotFoundError):
        # Re-raise these specific exceptions
        raise
    except Exception as e:
        masked_id = mask_contact_id(contact_id)
        logger.error(f"Error analyzing address for contact {masked_id}: {e}")
        from underwriting_validation.utils.validation_responses import format_error_response
        return {
            "contact_id": contact_id,
            "error": str(e),
            "analysis": None,
            "formatted_response": format_error_response(contact_id, f"Error analyzing address data for contact {contact_id}. {e}")
        }

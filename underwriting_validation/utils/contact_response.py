"""
Contact Response Utilities

This module provides utilities for contact response formatting including:
- Response formatting for different validation types
- Error response formatting
- Data formatting utilities
"""

from typing import Dict, Any


async def format_contact_response(contact: Dict[str, Any]) -> str:
    """
    Format hardship analysis results into a user-friendly response.
    
    Args:
        contact: Hardship analysis dictionary from analyze_contact_hardship
        
    Returns:
        Formatted string response
    """
    from underwriting_validation.utils.validation_responses import format_contact_response
    return await format_contact_response(contact)


async def format_budget_response(budget: Dict[str, Any]) -> str:
    """
    Format budget analysis results into a user-friendly response.
    
    Args:
        budget: Budget analysis dictionary from get_contact_budget_analysis
        
    Returns:
        Formatted string response
    """
    # If there's a formatted response already provided, use it
    if budget.get('formatted_response'):
        return budget['formatted_response']
    
    # If there's an error, return the error message
    if budget.get('error'):
        return f"Error analyzing budget data: {budget['error']}"
    
    # Use the budget analysis response formatter
    from underwriting_validation.utils.validation_responses import format_budget_analysis_response
    return await format_budget_analysis_response(budget)


async def format_address_response(address: Dict[str, Any]) -> str:
    """
    Format address analysis results into a user-friendly response.
    
    Args:
        address: Address analysis dictionary from analyze_contact_address
        
    Returns:
        Formatted string response
    """
    # If there's a formatted response already provided, use it
    if address.get('formatted_response'):
        return address['formatted_response']
    
    # If there's an error, return the error message
    if address.get('error'):
        return f"Error analyzing address data: {address['error']}"
    
    # Use the address analysis response formatter
    from underwriting_validation.utils.validation_responses import format_address_analysis_response
    return await format_address_analysis_response(address)


async def format_combined_validation_response(
    contact_id: int,
    hardship_data: Dict[str, Any],
    budget_data: Dict[str, Any],
    address_data: Dict[str, Any],
    hardship_analysis: Any,
    budget_analysis: Any,
    address_analysis: Any,
    combined_result: str
) -> str:
    """
    Format combined hardship, budget, and address analysis into a comprehensive response.
    
    Args:
        contact_id: The contact ID
        hardship_data: Hardship data dictionary
        budget_data: Budget data dictionary
        address_data: Address data dictionary
        hardship_analysis: Hardship analysis result
        budget_analysis: Budget analysis result
        address_analysis: Address analysis result
        combined_result: Combined validation result
        
    Returns:
        Formatted string response
    """
    from underwriting_validation.utils.validation_responses import format_combined_validation_response
    return await format_combined_validation_response(
        contact_id, hardship_data, budget_data, address_data,
        hardship_analysis, budget_analysis, address_analysis, combined_result
    )


async def format_error_response(contact_id: int, error_message: str, validation_type: str = "validation") -> str:
    """
    Format error response for contact operations.
    
    Args:
        contact_id: The contact ID
        error_message: The error message
        validation_type: The type of validation that failed
        
    Returns:
        Formatted error response
    """
    from underwriting_validation.utils.validation_responses import format_error_response
    return await format_error_response(contact_id, error_message, validation_type)


async def format_no_data_response(contact_id: int, validation_type: str = "validation") -> str:
    """
    Format no data response for contact operations.
    
    Args:
        contact_id: The contact ID
        validation_type: The type of validation
        
    Returns:
        Formatted no data response
    """
    from underwriting_validation.utils.validation_responses import format_no_data_response
    return await format_no_data_response(contact_id, validation_type)

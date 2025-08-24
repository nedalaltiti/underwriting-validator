"""
Validation Response Formats for Underwriting

This module provides a unified interface for all validation response formatting.
It imports from specialized modules to maintain clean separation of concerns.

For backward compatibility, all original functions are still available here.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import specialized formatters
from .hardship_responses import format_hardship_response, format_contact_response
from .budget_responses import format_budget_response, format_budget_analysis_response
from .address_responses import format_address_response, format_address_analysis_response
from .contract_responses import format_contract_response, format_contract_analysis_response
from .draft_responses import format_draft_response, format_draft_analysis_response
from .combined_responses import format_combined_validation_response
from .error_responses import (
    format_no_data_response, 
    format_error_response, 
    format_invalid_contact_id_response
)


class ValidationResult(Enum):
    """Enum for validation result types."""
    PASS = "pass"
    NO_PASS = "no_pass"
    MIXED = "mixed"
    NO_DATA = "no_data"
    ERROR = "error"


@dataclass
class ValidationResponse:
    """Structured validation response data."""
    contact_id: int
    result: ValidationResult
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Re-export all functions for backward compatibility
__all__ = [
    # Types
    'ValidationResult',
    'ValidationResponse',
    
    # Hardship responses
    'format_hardship_response',
    'format_contact_response',
    
    # Budget responses
    'format_budget_response',
    'format_budget_analysis_response',
    
    # Address responses
    'format_address_response',
    'format_address_analysis_response',
    
    # Contract responses
    'format_contract_response',
    'format_contract_analysis_response',
    
    # Draft responses
    'format_draft_response',
    'format_draft_analysis_response',
    
    # Combined responses
    'format_combined_validation_response',
    
    # Error responses
    'format_no_data_response',
    'format_error_response',
    'format_invalid_contact_id_response',
]

# Legacy ValidationResponseFormatter class for backward compatibility
class ValidationResponseFormatter:
    """Legacy formatter class for backward compatibility."""
    
    @staticmethod
    async def format_hardship_response(analysis, hardship_data):
        return await format_hardship_response(analysis, hardship_data)
    
    @staticmethod
    async def format_budget_response(analysis, budget_data):
        return await format_budget_response(analysis, budget_data)
    
    @staticmethod
    async def format_address_response(analysis, address_data):
        return await format_address_response(analysis, address_data)
    
    @staticmethod
    async def format_contract_response(analysis, contract_data):
        return await format_contract_response(analysis, contract_data)
    
    @staticmethod
    async def format_draft_response(analysis, draft_data):
        return await format_draft_response(analysis, draft_data)
    
    @staticmethod
    async def format_contact_response(contact):
        return await format_contact_response(contact)
    
    @staticmethod
    async def format_budget_analysis_response(budget):
        return await format_budget_analysis_response(budget)
    
    @staticmethod
    async def format_address_analysis_response(address):
        return await format_address_analysis_response(address)
    
    @staticmethod
    async def format_contract_analysis_response(contract):
        return await format_contract_analysis_response(contract)
    
    @staticmethod
    async def format_combined_validation_response(
        contact_id, hardship_data, budget_data, address_data,
        hardship_analysis, budget_analysis, address_analysis, combined_result
    ):
        return await format_combined_validation_response(
            contact_id, hardship_data, budget_data, address_data,
            hardship_analysis, budget_analysis, address_analysis, combined_result
        )
    
    @staticmethod
    async def format_no_data_response(contact_id, validation_type="validation"):
        return await format_no_data_response(contact_id, validation_type)
    
    @staticmethod
    async def format_error_response(contact_id, error_message, validation_type="validation"):
        return await format_error_response(contact_id, error_message, validation_type)
    
    @staticmethod
    async def format_invalid_contact_id_response(contact_id):
        return await format_invalid_contact_id_response(contact_id)
    
    @staticmethod
    async def format_credit_score_response(analysis, credit_score_data):
        from underwriting_validation.utils.credit_score_responses import format_credit_score_response
        return await format_credit_score_response(analysis, credit_score_data)
    
    @staticmethod
    async def format_credit_score_analysis_response(credit_score):
        from underwriting_validation.utils.credit_score_responses import format_credit_score_analysis_response
        return await format_credit_score_analysis_response(credit_score)





 
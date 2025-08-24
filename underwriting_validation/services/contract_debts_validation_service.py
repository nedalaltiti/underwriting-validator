"""
Contract Debts Validation Service for Underwriting

Validates debts-related data for contract validation.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


class DebtsValidationDataIn(BaseModel):
    """Input model for debts validation data."""
    contact_id: int
    forth_debt_count: Optional[int] = None
    contract_debt_count: Optional[int] = None


class DebtsValidationResult(Enum):
    """Enum for debts validation results."""
    MATCH = "Match"
    MISMATCH = "Mismatch"
    MISSING_VALUE = "Missing Value"


@dataclass
class DebtsValidationAnalysis:
    """Result of debts validation analysis."""
    debt_count_check: DebtsValidationResult
    forth_debt_count: Optional[int] = None
    contract_debt_count: Optional[int] = None


class ContractDebtsValidationService:
    """Service for validating debts-related data."""
    
    def __init__(self):
        """Initialize the debts validation service."""
        logger.info("ContractDebtsValidationService initialized")
    
    def validate_debt_count_match(self, forth_debt_count: Optional[int], contract_debt_count: Optional[int]) -> DebtsValidationResult:
        """Validate that debt counts match between contract and Forth."""
        if forth_debt_count is None or contract_debt_count is None:
            return DebtsValidationResult.MISSING_VALUE
        
        if forth_debt_count == contract_debt_count:
            return DebtsValidationResult.MATCH
        else:
            return DebtsValidationResult.MISMATCH
    
    async def analyze_debts_validity(
        self, 
        debts_data: DebtsValidationDataIn
    ) -> Result[DebtsValidationAnalysis]:
        """
        Analyze debts data and determine if validation passes.
        
        Args:
            debts_data: DebtsValidationDataIn model containing debts information
            
        Returns:
            Result containing DebtsValidationAnalysis
        """
        try:
            contact_id = debts_data.contact_id
            
            # Perform debts validation
            debt_count_check = self.validate_debt_count_match(debts_data.forth_debt_count, debts_data.contract_debt_count)
            
            analysis = DebtsValidationAnalysis(
                debt_count_check=debt_count_check,
                forth_debt_count=debts_data.forth_debt_count,
                contract_debt_count=debts_data.contract_debt_count
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Debts analysis completed for contact {masked_id}: {analysis.debt_count_check.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing debts validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    def format_debts_response(self, analysis: DebtsValidationAnalysis) -> str:
        """Format the debts analysis into a user-friendly response."""
        if analysis.debt_count_check == DebtsValidationResult.MATCH:
            return f"✅ Debts validation passed: Contract and Forth debt counts match"
        elif analysis.debt_count_check == DebtsValidationResult.MISMATCH:
            return f"❌ Debts validation failed: Contract and Forth debt counts do not match"
        else:
            return f"⚠️ Debts validation incomplete: Missing debt count data"

"""
Contract DOB Validation Service for Underwriting

Validates DOB-related data for contract validation.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from datetime import date
from pydantic import BaseModel

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


class DOBValidationDataIn(BaseModel):
    """Input model for DOB validation data."""
    contact_id: int
    forth_dob: Optional[date] = None
    contract_dob: Optional[date] = None
    age_plus_18_check: Optional[str] = None


class DOBValidationResult(Enum):
    """Enum for DOB validation results."""
    MATCH = "Match"
    MISMATCH = "Mismatch"
    MISSING_VALUE = "Missing Value"


class AgeValidationResult(Enum):
    """Enum for age validation results."""
    YES = "Yes"
    NO = "No"
    UNKNOWN_AGE = "Unknown Age"


@dataclass
class DOBValidationAnalysis:
    """Result of DOB validation analysis."""
    dob_check: DOBValidationResult
    age_plus_18_check: AgeValidationResult
    forth_dob: Optional[date] = None
    contract_dob: Optional[date] = None


class ContractDOBValidationService:
    """Service for validating DOB-related data."""
    
    def __init__(self):
        """Initialize the DOB validation service."""
        logger.info("ContractDOBValidationService initialized")
    
    def validate_dob_match(self, forth_dob: Optional[date], contract_dob: Optional[date]) -> DOBValidationResult:
        """Validate that DOB matches between Forth and credit report."""
        if not forth_dob or not contract_dob:
            return DOBValidationResult.MISSING_VALUE
        
        if forth_dob == contract_dob:
            return DOBValidationResult.MATCH
        else:
            return DOBValidationResult.MISMATCH
    
    def validate_age_18_plus(self, age_plus_18_check: Optional[str]) -> AgeValidationResult:
        """Validate that client is 18+ years old."""
        if not age_plus_18_check:
            return AgeValidationResult.UNKNOWN_AGE
        
        if age_plus_18_check == "Yes":
            return AgeValidationResult.YES
        elif age_plus_18_check == "No":
            return AgeValidationResult.NO
        else:
            return AgeValidationResult.UNKNOWN_AGE
    
    async def analyze_dob_validity(
        self, 
        dob_data: DOBValidationDataIn
    ) -> Result[DOBValidationAnalysis]:
        """
        Analyze DOB data and determine if validation passes.
        
        Args:
            dob_data: DOBValidationDataIn model containing DOB information
            
        Returns:
            Result containing DOBValidationAnalysis
        """
        try:
            contact_id = dob_data.contact_id
            
            # Perform DOB validations
            dob_check = self.validate_dob_match(dob_data.forth_dob, dob_data.contract_dob)
            age_plus_18_check = self.validate_age_18_plus(dob_data.age_plus_18_check)
            
            analysis = DOBValidationAnalysis(
                dob_check=dob_check,
                age_plus_18_check=age_plus_18_check,
                forth_dob=dob_data.forth_dob,
                contract_dob=dob_data.contract_dob
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"DOB analysis completed for contact {masked_id}: dob_check={dob_check.value}, age_check={age_plus_18_check.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing DOB validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    def format_dob_response(self, analysis: DOBValidationAnalysis) -> str:
        """Format the DOB analysis into a user-friendly response."""
        responses = []
        
        if analysis.dob_check == DOBValidationResult.MATCH:
            responses.append("✅ DOB validation passed")
        elif analysis.dob_check == DOBValidationResult.MISMATCH:
            responses.append("❌ DOB validation failed")
        else:
            responses.append("⚠️ DOB validation incomplete")
        
        if analysis.age_plus_18_check == AgeValidationResult.YES:
            responses.append("✅ Age validation passed (18+)")
        elif analysis.age_plus_18_check == AgeValidationResult.NO:
            responses.append("❌ Age validation failed (<18)")
        else:
            responses.append("⚠️ Age validation incomplete")
        
        return " | ".join(responses)

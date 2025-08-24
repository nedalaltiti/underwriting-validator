"""
Credit Score Validation Service for Underwriting

Validates credit scores and determines if they meet minimum requirements.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


class CreditScoreDataIn(BaseModel):
    """Input model for credit score validation data."""
    contact_id: int
    equifax: float = Field(ge=0)
    experian: float = Field(ge=0)
    transunion: float = Field(ge=0)
    credit_score: float = Field(ge=0)
    has_credit_data: bool = True


class CreditScoreValidity(Enum):
    """Enum for credit score validation results."""
    PASS = "pass"
    NO_PASS = "no_pass"
    NO_DATA = "no_data"


@dataclass
class CreditScoreAnalysis:
    """Result of credit score validation analysis."""
    result: CreditScoreValidity  # "pass", "no_pass", or "no_data"
    reason: str
    credit_score: float
    equifax: float
    experian: float
    transunion: float
    has_credit_data: bool
    credit_score_status: str  # "missing", "low", or "acceptable"


class CreditScoreValidationService:
    """Service for validating credit scores and determining if they meet minimum requirements."""
    
    def __init__(self):
        """Initialize the credit score validation service."""
        self.minimum_credit_score = 500  # Minimum acceptable credit score
        logger.info("CreditScoreValidationService initialized")
    
    async def analyze_credit_score_validity(
        self, 
        credit_score_data: CreditScoreDataIn
    ) -> Result[CreditScoreAnalysis]:
        """
        Analyze credit score data and determine if it meets minimum requirements.
        
        Args:
            credit_score_data: CreditScoreDataIn model containing credit score information
            
        Returns:
            Result containing CreditScoreAnalysis
        """
        try:
            # Extract credit score values from the validated model
            equifax = credit_score_data.equifax
            experian = credit_score_data.experian
            transunion = credit_score_data.transunion
            total_credit_score = credit_score_data.credit_score
            has_credit_data = credit_score_data.has_credit_data
            
            # Determine validation result with enhanced handling for missing/zero credit scores
            if not has_credit_data or total_credit_score == 0:
                result = CreditScoreValidity.NO_DATA
                if not has_credit_data:
                    reason = "Credit score data is missing or unavailable"
                else:
                    reason = "Credit score data exists but all values are zero or invalid"
                credit_score_status = "missing"
            elif total_credit_score < self.minimum_credit_score:
                result = CreditScoreValidity.NO_PASS
                reason = f"Credit score is below minimum threshold of {self.minimum_credit_score} (Total: {total_credit_score})"
                credit_score_status = "low"
            else:
                result = CreditScoreValidity.PASS
                reason = f"Credit score meets minimum requirements (Total: {total_credit_score})"
                credit_score_status = "acceptable"
            
            analysis = CreditScoreAnalysis(
                result=result,
                reason=reason,
                credit_score=total_credit_score,
                equifax=equifax,
                experian=experian,
                transunion=transunion,
                has_credit_data=has_credit_data,
                credit_score_status=credit_score_status
            )
            
            masked_id = mask_contact_id(credit_score_data.contact_id)
            logger.info(f"Credit score analysis completed for contact {masked_id}: {analysis.result.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing credit score validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    async def format_credit_score_response(self, analysis: CreditScoreAnalysis, credit_score_data: CreditScoreDataIn) -> str:
        """Format the credit score analysis into a user-friendly response."""
        from underwriting_validation.utils.validation_responses import format_credit_score_response
        return await format_credit_score_response(analysis, credit_score_data)

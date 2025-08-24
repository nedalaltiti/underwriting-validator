"""
Draft Validation Service for Underwriting

Uses database queries to analyze draft data and determine if monthly payments meet the $250 minimum requirement.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


class MonthlyPayment(BaseModel):
    """Model for monthly payment data."""
    year: int
    month: int
    total_payment: float = Field(ge=0)
    over_250: bool


class DraftDataIn(BaseModel):
    """Input model for draft validation data."""
    contact_id: int
    monthly_payments: List[MonthlyPayment] = Field(default_factory=list)
    total_payments: float = Field(ge=0)
    payment_count: int = Field(ge=0)
    months_with_data: int = Field(ge=0)


class DraftValidity(Enum):
    """Enum for draft validation results."""
    PASS = "pass"
    NO_PASS = "no_pass"


@dataclass
class DraftAnalysis:
    """Result of draft validation analysis."""
    result: DraftValidity  # "pass" or "no_pass"
    reason: str
    monthly_payments: List[MonthlyPayment]
    total_payments: float
    payment_count: int
    months_with_data: int
    months_over_250: int
    months_under_250: int
    average_monthly_payment: float
    minimum_monthly_payment: float


class DraftValidationService:
    """Service for validating draft data and determining if payments meet minimum requirements."""
    
    def __init__(self):
        """Initialize the draft validation service."""
        logger.info("DraftValidationService initialized")
    
    async def analyze_draft_validity(
        self, 
        draft_data: DraftDataIn
    ) -> Result[DraftAnalysis]:
        """
        Analyze draft data and determine if monthly payments meet the $250 minimum requirement.
        
        Args:
            draft_data: DraftDataIn model containing draft information
            
        Returns:
            Result containing DraftAnalysis
        """
        try:
            # Extract draft values from the validated model
            monthly_payments = draft_data.monthly_payments
            total_payments = draft_data.total_payments
            payment_count = draft_data.payment_count
            months_with_data = draft_data.months_with_data
            
            # Calculate statistics
            months_over_250 = sum(1 for payment in monthly_payments if payment.over_250)
            months_under_250 = months_with_data - months_over_250
            
            # Calculate average monthly payment
            average_monthly_payment = total_payments / months_with_data if months_with_data > 0 else 0
            
            # Find minimum monthly payment
            minimum_monthly_payment = min([payment.total_payment for payment in monthly_payments]) if monthly_payments else 0
            
            # Determine if all months meet the $250 minimum requirement
            if months_with_data == 0:
                result = DraftValidity.NO_PASS
                reason = "No payment data available for analysis"
            elif months_under_250 == 0 and months_over_250 > 0:
                result = DraftValidity.PASS
                reason = f"All {months_over_250} months meet the $250 minimum payment requirement (Average: ${average_monthly_payment:,.2f})"
            else:
                result = DraftValidity.NO_PASS
                reason = f"{months_under_250} out of {months_with_data} months do not meet the $250 minimum payment requirement (Minimum: ${minimum_monthly_payment:,.2f})"
            
            analysis = DraftAnalysis(
                result=result,
                reason=reason,
                monthly_payments=monthly_payments,
                total_payments=total_payments,
                payment_count=payment_count,
                months_with_data=months_with_data,
                months_over_250=months_over_250,
                months_under_250=months_under_250,
                average_monthly_payment=average_monthly_payment,
                minimum_monthly_payment=minimum_monthly_payment
            )
            
            masked_id = mask_contact_id(draft_data.contact_id)
            logger.info(f"Draft analysis completed for contact {masked_id}: {analysis.result.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing draft validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    def format_draft_response(self, analysis: DraftAnalysis, draft_data: DraftDataIn) -> str:
        """Format the draft analysis into a user-friendly response."""
        from underwriting_validation.utils.validation_responses import format_draft_response
        return format_draft_response(analysis, draft_data)

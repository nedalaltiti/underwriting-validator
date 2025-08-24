"""
Contract Email Validation Service for Underwriting

Validates email-related data for contract validation.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.validation_base import ContractValidationServiceBase


class EmailValidationDataIn(BaseModel):
    """Input model for email validation data."""
    contact_id: int
    forth_email: Optional[str] = None
    contract_email: Optional[str] = None


class EmailValidationResult(Enum):
    """Enum for email validation results."""
    MATCH = "Match"
    MISMATCH = "Mismatch"
    MISSING_VALUE = "Missing Value"


@dataclass
class EmailValidationAnalysis:
    """Result of email validation analysis."""
    email_check: EmailValidationResult
    forth_email: Optional[str] = None
    contract_email: Optional[str] = None


class ContractEmailValidationService(ContractValidationServiceBase):
    """Service for validating email-related data."""
    
    def __init__(self):
        """Initialize the email validation service."""
        super().__init__("ContractEmailValidationService")
    
    def get_validation_type(self) -> str:
        """Return the validation type name."""
        return "email"
    
    def validate_email_match(self, forth_email: Optional[str], contract_email: Optional[str]) -> EmailValidationResult:
        """Validate that Forth email matches contract email."""
        # Use base class normalization
        forth_normalized = self.normalize_string_field(forth_email)
        contract_normalized = self.normalize_string_field(contract_email)
        
        if not forth_normalized or not contract_normalized:
            return EmailValidationResult.MISSING_VALUE
        
        # Convert to lowercase for comparison
        forth_lower = forth_normalized.lower()
        contract_lower = contract_normalized.lower()
        
        if forth_lower == contract_lower:
            return EmailValidationResult.MATCH
        else:
            return EmailValidationResult.MISMATCH
    
    async def analyze_email_validity(
        self, 
        email_data: EmailValidationDataIn
    ) -> Result[EmailValidationAnalysis]:
        """
        Analyze email data and determine if validation passes.
        
        Args:
            email_data: EmailValidationDataIn model containing email information
            
        Returns:
            Result containing EmailValidationAnalysis
        """
        try:
            contact_id = email_data.contact_id
            forth_email = email_data.forth_email
            contract_email = email_data.contract_email
            
            # Perform email validation
            email_check = self.validate_email_match(forth_email, contract_email)
            
            analysis = EmailValidationAnalysis(
                email_check=email_check,
                forth_email=forth_email,
                contract_email=contract_email
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Email analysis completed for contact {masked_id}: {analysis.email_check.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing email validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    def format_email_response(self, analysis: EmailValidationAnalysis) -> str:
        """Format the email analysis into a user-friendly response."""
        if analysis.email_check == EmailValidationResult.MATCH:
            return f"✅ Email validation passed: Forth and contract emails match"
        elif analysis.email_check == EmailValidationResult.MISMATCH:
            return f"❌ Email validation failed: Forth and contract emails do not match"
        else:
            return f"⚠️ Email validation incomplete: Missing email data"

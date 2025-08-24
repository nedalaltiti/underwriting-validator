"""
Contract SSN Validation Service for Underwriting

Validates SSN-related data for contract validation.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


class SSNValidationDataIn(BaseModel):
    """Input model for SSN validation data."""
    contact_id: int
    payment_gateway_agreement_client_ssn: Optional[str] = None
    legal_plan_agreement_client_ssn: Optional[str] = None
    power_of_attorney_client_ssn: Optional[str] = None
    credit_report_ssn: Optional[str] = None


class SSNValidationResult(Enum):
    """Enum for SSN validation results."""
    MATCH = "Match"
    MISMATCH = "Mismatch"
    MISSING_VALUE = "Missing Value"


@dataclass
class SSNValidationAnalysis:
    """Result of SSN validation analysis."""
    ssn_check: SSNValidationResult
    payment_gateway_agreement_client_ssn: Optional[str] = None
    legal_plan_agreement_client_ssn: Optional[str] = None
    power_of_attorney_client_ssn: Optional[str] = None
    credit_report_ssn: Optional[str] = None


class ContractSSNValidationService:
    """Service for validating SSN-related data."""
    
    def __init__(self):
        """Initialize the SSN validation service."""
        logger.info("ContractSSNValidationService initialized")
    
    def validate_ssn_match(self, contract_data: SSNValidationDataIn) -> SSNValidationResult:
        """Validate that SSN matches across all sources."""
        if not contract_data.legal_plan_agreement_client_ssn or not contract_data.power_of_attorney_client_ssn or not contract_data.credit_report_ssn:
            return SSNValidationResult.MISSING_VALUE
        
        # Check if all SSNs match
        if (contract_data.legal_plan_agreement_client_ssn == contract_data.power_of_attorney_client_ssn and 
            contract_data.legal_plan_agreement_client_ssn == contract_data.credit_report_ssn and
            contract_data.payment_gateway_agreement_client_ssn and
            contract_data.legal_plan_agreement_client_ssn[-4:] == contract_data.payment_gateway_agreement_client_ssn[-4:]):
            return SSNValidationResult.MATCH
        else:
            return SSNValidationResult.MISMATCH
    
    async def analyze_ssn_validity(
        self, 
        ssn_data: SSNValidationDataIn
    ) -> Result[SSNValidationAnalysis]:
        """
        Analyze SSN data and determine if validation passes.
        
        Args:
            ssn_data: SSNValidationDataIn model containing SSN information
            
        Returns:
            Result containing SSNValidationAnalysis
        """
        try:
            contact_id = ssn_data.contact_id
            
            # Perform SSN validation
            ssn_check = self.validate_ssn_match(ssn_data)
            
            analysis = SSNValidationAnalysis(
                ssn_check=ssn_check,
                payment_gateway_agreement_client_ssn=ssn_data.payment_gateway_agreement_client_ssn,
                legal_plan_agreement_client_ssn=ssn_data.legal_plan_agreement_client_ssn,
                power_of_attorney_client_ssn=ssn_data.power_of_attorney_client_ssn,
                credit_report_ssn=ssn_data.credit_report_ssn
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"SSN analysis completed for contact {masked_id}: {analysis.ssn_check.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing SSN validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    def format_ssn_response(self, analysis: SSNValidationAnalysis) -> str:
        """Format the SSN analysis into a user-friendly response."""
        if analysis.ssn_check == SSNValidationResult.MATCH:
            return f"✅ SSN validation passed: All SSN sources match"
        elif analysis.ssn_check == SSNValidationResult.MISMATCH:
            return f"❌ SSN validation failed: SSN sources do not match"
        else:
            return f"⚠️ SSN validation incomplete: Missing SSN data"

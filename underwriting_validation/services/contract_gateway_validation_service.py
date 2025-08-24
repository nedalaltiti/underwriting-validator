"""
Contract Gateway Validation Service for Underwriting

Validates gateway-related data for contract validation.
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


class GatewayValidationDataIn(BaseModel):
    """Input model for gateway validation data."""
    contact_id: int
    gateway_client_signature: Optional[str] = None
    contract_payment_count: Optional[int] = None
    forth_payment_count: Optional[int] = None
    payment_details: Optional[List[Dict[str, Any]]] = None


class GatewayValidationResult(Enum):
    """Enum for gateway validation results."""
    MATCH = "Match"
    MISMATCH = "Mismatch"
    VALID = "Valid"
    INVALID = "Invalid"
    MISSING_VALUE = "Missing Value"


@dataclass
class GatewayValidationAnalysis:
    """Result of gateway validation analysis."""
    gateway_signature_check: GatewayValidationResult
    payment_count_check: GatewayValidationResult
    payment_amounts_check: GatewayValidationResult
    payment_dates_check: GatewayValidationResult
    gateway_client_signature: Optional[str] = None
    contract_payment_count: Optional[int] = None
    forth_payment_count: Optional[int] = None
    payment_details: Optional[List[Dict[str, Any]]] = None


class ContractGatewayValidationService:
    """Service for validating gateway-related data."""
    
    def __init__(self):
        """Initialize the gateway validation service."""
        logger.info("ContractGatewayValidationService initialized")
    
    def validate_gateway_signature(self, gateway_signature: Optional[str]) -> GatewayValidationResult:
        """Validate that gateway signature exists and is valid."""
        if not gateway_signature or gateway_signature == '':
            return GatewayValidationResult.MISSING_VALUE
        
        # Check for invalid characters (dots/dashes) in signature
        invalid_chars = ['.', '-']
        signature = gateway_signature.strip()
        if any(char in signature for char in invalid_chars):
            return GatewayValidationResult.INVALID
        
        return GatewayValidationResult.VALID
    
    def validate_payment_count(self, contract_count: Optional[int], forth_count: Optional[int]) -> GatewayValidationResult:
        """Validate that payment counts match between contract and Forth."""
        if contract_count is None or forth_count is None:
            return GatewayValidationResult.MISSING_VALUE
        
        if contract_count == forth_count:
            return GatewayValidationResult.MATCH
        else:
            return GatewayValidationResult.MISMATCH
    
    def validate_payment_amounts_and_dates(self, payment_details: Optional[List[Dict[str, Any]]]) -> tuple[GatewayValidationResult, GatewayValidationResult]:
        """Validate payment amounts and dates from payment details."""
        if not payment_details or len(payment_details) == 0:
            return GatewayValidationResult.MISSING_VALUE, GatewayValidationResult.MISSING_VALUE
        
        # Check if all payments have matching amounts and dates
        all_amounts_match = True
        all_dates_match = True
        
        for payment in payment_details:
            if payment.get('amount_check') == 'Mismatch':
                all_amounts_match = False
            if payment.get('date_check') == 'Mismatch':
                all_dates_match = False
        
        amounts_check = GatewayValidationResult.MATCH if all_amounts_match else GatewayValidationResult.MISMATCH
        dates_check = GatewayValidationResult.MATCH if all_dates_match else GatewayValidationResult.MISMATCH
        
        return amounts_check, dates_check
    
    async def analyze_gateway_validity(
        self, 
        gateway_data: GatewayValidationDataIn
    ) -> Result[GatewayValidationAnalysis]:
        """
        Analyze gateway data and determine if validation passes.
        
        Args:
            gateway_data: GatewayValidationDataIn model containing gateway information
            
        Returns:
            Result containing GatewayValidationAnalysis
        """
        try:
            contact_id = gateway_data.contact_id
            
            # Perform gateway validations
            gateway_signature_check = self.validate_gateway_signature(gateway_data.gateway_client_signature)
            payment_count_check = self.validate_payment_count(gateway_data.contract_payment_count, gateway_data.forth_payment_count)
            payment_amounts_check, payment_dates_check = self.validate_payment_amounts_and_dates(gateway_data.payment_details)
            
            analysis = GatewayValidationAnalysis(
                gateway_signature_check=gateway_signature_check,
                payment_count_check=payment_count_check,
                payment_amounts_check=payment_amounts_check,
                payment_dates_check=payment_dates_check,
                gateway_client_signature=gateway_data.gateway_client_signature,
                contract_payment_count=gateway_data.contract_payment_count,
                forth_payment_count=gateway_data.forth_payment_count,
                payment_details=gateway_data.payment_details
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Gateway analysis completed for contact {masked_id}: signature={gateway_signature_check.value}, count={payment_count_check.value}, amounts={payment_amounts_check.value}, dates={payment_dates_check.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing gateway validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    async def format_gateway_response(self, analysis: GatewayValidationAnalysis) -> str:
        """Format the gateway analysis into a user-friendly response."""
        responses = []
        
        if analysis.gateway_signature_check == GatewayValidationResult.VALID:
            responses.append("✅ Gateway signature validation passed")
        elif analysis.gateway_signature_check == GatewayValidationResult.INVALID:
            responses.append("❌ Gateway signature validation failed")
        else:
            responses.append("⚠️ Gateway signature validation incomplete")
        
        if analysis.payment_count_check == GatewayValidationResult.MATCH:
            responses.append("✅ Payment count validation passed")
        elif analysis.payment_count_check == GatewayValidationResult.MISMATCH:
            responses.append("❌ Payment count validation failed")
        else:
            responses.append("⚠️ Payment count validation incomplete")
        
        if analysis.payment_amounts_check == GatewayValidationResult.MATCH:
            responses.append("✅ Payment amounts validation passed")
        elif analysis.payment_amounts_check == GatewayValidationResult.MISMATCH:
            responses.append("❌ Payment amounts validation failed")
        else:
            responses.append("⚠️ Payment amounts validation incomplete")
        
        if analysis.payment_dates_check == GatewayValidationResult.MATCH:
            responses.append("✅ Payment dates validation passed")
        elif analysis.payment_dates_check == GatewayValidationResult.MISMATCH:
            responses.append("❌ Payment dates validation failed")
        else:
            responses.append("⚠️ Payment dates validation incomplete")
        
        return " | ".join(responses)

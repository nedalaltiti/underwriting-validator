"""
Contract Signature Validation Service for Underwriting

Validates signature-related data for contract validation.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


class SignatureValidationDataIn(BaseModel):
    """Input model for signature validation data."""
    contact_id: int
    client_signature: Optional[str] = None
    coclient_signature: Optional[str] = None


class SignatureValidationResult(Enum):
    """Enum for signature validation results."""
    VALID = "Valid"
    INVALID = "Invalid"
    MISSING_VALUE = "Missing Value"


@dataclass
class SignatureValidationAnalysis:
    """Result of signature validation analysis."""
    signature_check: SignatureValidationResult
    client_signature: Optional[str] = None
    coclient_signature: Optional[str] = None


class ContractSignatureValidationService:
    """Service for validating signature-related data."""
    
    def __init__(self):
        """Initialize the signature validation service."""
        logger.info("ContractSignatureValidationService initialized")
    
    def validate_signatures(self, client_signature: Optional[str], coclient_signature: Optional[str]) -> SignatureValidationResult:
        """Validate signatures follow Forth's requirements."""
        if not client_signature and not coclient_signature:
            return SignatureValidationResult.MISSING_VALUE
        
        # Check for invalid characters (dots/dashes) in signatures
        invalid_chars = ['.', '-']
        
        if client_signature:
            client_sig = client_signature.strip()
            if any(char in client_sig for char in invalid_chars):
                return SignatureValidationResult.INVALID
        
        if coclient_signature:
            coclient_sig = coclient_signature.strip()
            if any(char in coclient_sig for char in invalid_chars):
                return SignatureValidationResult.INVALID
        
        return SignatureValidationResult.VALID
    
    async def analyze_signature_validity(
        self, 
        signature_data: SignatureValidationDataIn
    ) -> Result[SignatureValidationAnalysis]:
        """
        Analyze signature data and determine if validation passes.
        
        Args:
            signature_data: SignatureValidationDataIn model containing signature information
            
        Returns:
            Result containing SignatureValidationAnalysis
        """
        try:
            contact_id = signature_data.contact_id
            client_signature = signature_data.client_signature
            coclient_signature = signature_data.coclient_signature
            
            # Perform signature validation
            signature_check = self.validate_signatures(client_signature, coclient_signature)
            
            analysis = SignatureValidationAnalysis(
                signature_check=signature_check,
                client_signature=client_signature,
                coclient_signature=coclient_signature
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Signature analysis completed for contact {masked_id}: {analysis.signature_check.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing signature validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    def format_signature_response(self, analysis: SignatureValidationAnalysis) -> str:
        """Format the signature analysis into a user-friendly response."""
        if analysis.signature_check == SignatureValidationResult.VALID:
            return f"✅ Signature validation passed: Signatures are valid"
        elif analysis.signature_check == SignatureValidationResult.INVALID:
            return f"❌ Signature validation failed: Signatures contain invalid characters"
        else:
            return f"⚠️ Signature validation incomplete: Missing signature data"

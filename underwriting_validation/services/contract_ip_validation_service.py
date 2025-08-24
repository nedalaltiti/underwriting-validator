"""
Contract IP Validation Service for Underwriting

Validates IP address-related data for contract validation.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


class IPValidationDataIn(BaseModel):
    """Input model for IP validation data."""
    contact_id: int
    sender_ip_address: Optional[str] = None
    signer_ip_address: Optional[str] = None


class IPValidationResult(Enum):
    """Enum for IP validation results."""
    MATCH = "Match"
    MISMATCH = "Mismatch"
    MISSING_VALUE = "Missing Value"


@dataclass
class IPValidationAnalysis:
    """Result of IP validation analysis."""
    ip_check: IPValidationResult
    sender_ip_address: Optional[str] = None
    signer_ip_address: Optional[str] = None


class ContractIPValidationService:
    """Service for validating IP address-related data."""
    
    def __init__(self):
        """Initialize the IP validation service."""
        logger.info("ContractIPValidationService initialized")
    
    def validate_ip_addresses(self, sender_ip: Optional[str], signer_ip: Optional[str]) -> IPValidationResult:
        """Validate that sender and signer IP addresses differ."""
        if not sender_ip or not signer_ip:
            return IPValidationResult.MISSING_VALUE
        
        # Normalize IP addresses by trimming whitespace
        sender_ip = sender_ip.strip()
        signer_ip = signer_ip.strip()
        
        if sender_ip == signer_ip:
            return IPValidationResult.MISMATCH
        else:
            return IPValidationResult.MATCH
    
    async def analyze_ip_validity(
        self, 
        ip_data: IPValidationDataIn
    ) -> Result[IPValidationAnalysis]:
        """
        Analyze IP data and determine if validation passes.
        
        Args:
            ip_data: IPValidationDataIn model containing IP information
            
        Returns:
            Result containing IPValidationAnalysis
        """
        try:
            contact_id = ip_data.contact_id
            sender_ip = ip_data.sender_ip_address
            signer_ip = ip_data.signer_ip_address
            
            # Perform IP validation
            ip_check = self.validate_ip_addresses(sender_ip, signer_ip)
            
            analysis = IPValidationAnalysis(
                ip_check=ip_check,
                sender_ip_address=sender_ip,
                signer_ip_address=signer_ip
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"IP analysis completed for contact {masked_id}: {analysis.ip_check.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing IP validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    def format_ip_response(self, analysis: IPValidationAnalysis) -> str:
        """Format the IP analysis into a user-friendly response."""
        if analysis.ip_check == IPValidationResult.MATCH:
            return f"✅ IP validation passed: Sender and signer IP addresses are different"
        elif analysis.ip_check == IPValidationResult.MISMATCH:
            return f"❌ IP validation failed: Sender and signer IP addresses are the same"
        else:
            return f"⚠️ IP validation incomplete: Missing IP address data"

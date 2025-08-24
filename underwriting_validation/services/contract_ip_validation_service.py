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
from underwriting_validation.utils.validation_base import ContractValidationServiceBase


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


class ContractIPValidationService(ContractValidationServiceBase):
    """Service for validating IP address-related data."""
    
    def __init__(self):
        """Initialize the IP validation service."""
        super().__init__("ContractIPValidationService")
    
    def get_validation_type(self) -> str:
        """Return the validation type name."""
        return "IP"
    
    def validate_ip_addresses(self, sender_ip: Optional[str], signer_ip: Optional[str]) -> IPValidationResult:
        """Validate that sender and signer IP addresses differ."""
        # Use base class normalization
        sender_normalized = self.normalize_string_field(sender_ip)
        signer_normalized = self.normalize_string_field(signer_ip)
        
        if not sender_normalized or not signer_normalized:
            return IPValidationResult.MISSING_VALUE
        
        if sender_normalized == signer_normalized:
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
        def perform_analysis():
            # Perform IP validation
            ip_check = self.validate_ip_addresses(
                ip_data.sender_ip_address, 
                ip_data.signer_ip_address
            )
            
            analysis = IPValidationAnalysis(
                ip_check=ip_check,
                sender_ip_address=ip_data.sender_ip_address,
                signer_ip_address=ip_data.signer_ip_address
            )
            
            # Log completion using base class method
            self.log_analysis_completion(ip_data.contact_id, analysis.ip_check.value)
            return analysis
        
        # Use base class safe execution
        return self.safe_execute("IP validation analysis", ip_data.contact_id, perform_analysis)
    
    def format_ip_response(self, analysis: IPValidationAnalysis) -> str:
        """Format the IP analysis into a user-friendly response."""
        return self.format_validation_response(
            analysis.ip_check,
            "IP validation passed: Sender and signer IP addresses are different",
            "IP validation failed: Sender and signer IP addresses are the same", 
            "IP validation incomplete: Missing IP address data"
        )

"""
Contract VLP Validation Service for Underwriting

Validates VLP (Voluntary Legal Plan) related data for contract validation.
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


class VLPValidationDataIn(BaseModel):
    """Input model for VLP validation data."""
    contact_id: int
    contract_name: Optional[str] = None
    forth_name: Optional[str] = None
    contract_ssn: Optional[str] = None
    forth_ssn: Optional[str] = None
    contract_dob: Optional[date] = None
    forth_dob: Optional[date] = None
    legal_setup_fee_snapshot: Optional[str] = None
    legal_monthly_fee_snapshot: Optional[str] = None
    legal_setup_fee_enrollment: Optional[str] = None
    legal_monthly_fee_enrollment: Optional[str] = None
    plan_name: Optional[str] = None


class VLPValidationResult(Enum):
    """Enum for VLP validation results."""
    MATCH = "Match"
    MISMATCH = "Mismatch"
    VALID = "Valid"
    INVALID = "Invalid"
    MISSING_VALUE = "Missing Value"


@dataclass
class VLPValidationAnalysis:
    """Result of VLP validation analysis."""
    name_check: VLPValidationResult
    ssn_check: VLPValidationResult
    dob_check: VLPValidationResult
    fees_check: VLPValidationResult
    plan_check: VLPValidationResult
    contract_name: Optional[str] = None
    forth_name: Optional[str] = None
    contract_ssn: Optional[str] = None
    forth_ssn: Optional[str] = None
    contract_dob: Optional[date] = None
    forth_dob: Optional[date] = None
    legal_setup_fee_snapshot: Optional[str] = None
    legal_monthly_fee_snapshot: Optional[str] = None
    legal_setup_fee_enrollment: Optional[str] = None
    legal_monthly_fee_enrollment: Optional[str] = None
    plan_name: Optional[str] = None


class ContractVLPValidationService:
    """Service for validating VLP-related data."""
    
    def __init__(self):
        """Initialize the VLP validation service."""
        logger.info("ContractVLPValidationService initialized")
    
    def validate_vlp_name_match(self, contract_name: Optional[str], forth_name: Optional[str]) -> VLPValidationResult:
        """Validate that contract name matches Forth name."""
        if not contract_name or contract_name == '' or not forth_name or forth_name == '':
            return VLPValidationResult.MISSING_VALUE
        
        # Normalize names by trimming whitespace
        contract_name = contract_name.strip()
        forth_name = forth_name.strip()
        
        if contract_name == forth_name:
            return VLPValidationResult.MATCH
        else:
            return VLPValidationResult.MISMATCH
    
    def validate_vlp_ssn_match(self, contract_ssn: Optional[str], forth_ssn: Optional[str]) -> VLPValidationResult:
        """Validate that contract SSN matches Forth SSN."""
        if not contract_ssn or contract_ssn == '' or not forth_ssn or forth_ssn == '':
            return VLPValidationResult.MISSING_VALUE
        
        # Normalize SSNs by trimming whitespace
        contract_ssn = contract_ssn.strip()
        forth_ssn = forth_ssn.strip()
        
        if contract_ssn == forth_ssn:
            return VLPValidationResult.MATCH
        else:
            return VLPValidationResult.MISMATCH
    
    def validate_vlp_dob_match(self, contract_dob: Optional[date], forth_dob: Optional[date]) -> VLPValidationResult:
        """Validate that contract DOB matches Forth DOB."""
        if not contract_dob or not forth_dob:
            return VLPValidationResult.MISSING_VALUE
        
        # Direct date comparison
        if contract_dob == forth_dob:
            return VLPValidationResult.MATCH
        else:
            return VLPValidationResult.MISMATCH
    
    def validate_vlp_fees(self, setup_fee_snapshot: Optional[str], monthly_fee_snapshot: Optional[str],
                         setup_fee_enrollment: Optional[str], monthly_fee_enrollment: Optional[str]) -> VLPValidationResult:
        """Validate that VLP fees exist in both client snapshot and enrollment tab."""
        has_snapshot_fees = setup_fee_snapshot or monthly_fee_snapshot
        has_enrollment_fees = setup_fee_enrollment or monthly_fee_enrollment
        
        if not has_snapshot_fees and not has_enrollment_fees:
            return VLPValidationResult.MISSING_VALUE
        
        if has_snapshot_fees and has_enrollment_fees:
            return VLPValidationResult.VALID
        else:
            return VLPValidationResult.INVALID  # Only one source has fees
    
    def validate_vlp_plan_name(self, plan_name: Optional[str]) -> VLPValidationResult:
        """Validate that enrollment plan name contains 'w/VLP'."""
        if not plan_name or plan_name == '':
            return VLPValidationResult.MISSING_VALUE
        
        plan_name_lower = plan_name.strip().lower()
        if 'w/vlp' in plan_name_lower:
            return VLPValidationResult.VALID
        else:
            return VLPValidationResult.INVALID
    
    async def analyze_vlp_validity(
        self, 
        vlp_data: VLPValidationDataIn
    ) -> Result[VLPValidationAnalysis]:
        """
        Analyze VLP data and determine if validation passes.
        
        Args:
            vlp_data: VLPValidationDataIn model containing VLP information
            
        Returns:
            Result containing VLPValidationAnalysis
        """
        try:
            contact_id = vlp_data.contact_id
            
            # Perform VLP validations
            name_check = self.validate_vlp_name_match(vlp_data.contract_name, vlp_data.forth_name)
            ssn_check = self.validate_vlp_ssn_match(vlp_data.contract_ssn, vlp_data.forth_ssn)
            dob_check = self.validate_vlp_dob_match(vlp_data.contract_dob, vlp_data.forth_dob)
            fees_check = self.validate_vlp_fees(
                vlp_data.legal_setup_fee_snapshot,
                vlp_data.legal_monthly_fee_snapshot,
                vlp_data.legal_setup_fee_enrollment,
                vlp_data.legal_monthly_fee_enrollment
            )
            plan_check = self.validate_vlp_plan_name(vlp_data.plan_name)
            
            analysis = VLPValidationAnalysis(
                name_check=name_check,
                ssn_check=ssn_check,
                dob_check=dob_check,
                fees_check=fees_check,
                plan_check=plan_check,
                contract_name=vlp_data.contract_name,
                forth_name=vlp_data.forth_name,
                contract_ssn=vlp_data.contract_ssn,
                forth_ssn=vlp_data.forth_ssn,
                contract_dob=vlp_data.contract_dob,
                forth_dob=vlp_data.forth_dob,
                legal_setup_fee_snapshot=vlp_data.legal_setup_fee_snapshot,
                legal_monthly_fee_snapshot=vlp_data.legal_monthly_fee_snapshot,
                legal_setup_fee_enrollment=vlp_data.legal_setup_fee_enrollment,
                legal_monthly_fee_enrollment=vlp_data.legal_monthly_fee_enrollment,
                plan_name=vlp_data.plan_name
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"VLP analysis completed for contact {masked_id}: name={name_check.value}, ssn={ssn_check.value}, dob={dob_check.value}, fees={fees_check.value}, plan={plan_check.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing VLP validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    async def format_vlp_response(self, analysis: VLPValidationAnalysis) -> str:
        """Format the VLP analysis into a user-friendly response."""
        responses = []
        
        if analysis.name_check == VLPValidationResult.MATCH:
            responses.append("✅ Name validation passed")
        elif analysis.name_check == VLPValidationResult.MISMATCH:
            responses.append("❌ Name validation failed")
        else:
            responses.append("⚠️ Name validation incomplete")
        
        if analysis.ssn_check == VLPValidationResult.MATCH:
            responses.append("✅ SSN validation passed")
        elif analysis.ssn_check == VLPValidationResult.MISMATCH:
            responses.append("❌ SSN validation failed")
        else:
            responses.append("⚠️ SSN validation incomplete")
        
        if analysis.dob_check == VLPValidationResult.MATCH:
            responses.append("✅ DOB validation passed")
        elif analysis.dob_check == VLPValidationResult.MISMATCH:
            responses.append("❌ DOB validation failed")
        else:
            responses.append("⚠️ DOB validation incomplete")
        
        if analysis.fees_check == VLPValidationResult.VALID:
            responses.append("✅ Fees validation passed")
        elif analysis.fees_check == VLPValidationResult.INVALID:
            responses.append("❌ Fees validation failed")
        else:
            responses.append("⚠️ Fees validation incomplete")
        
        if analysis.plan_check == VLPValidationResult.VALID:
            responses.append("✅ Plan validation passed")
        elif analysis.plan_check == VLPValidationResult.INVALID:
            responses.append("❌ Plan validation failed")
        else:
            responses.append("⚠️ Plan validation incomplete")
        
        return " | ".join(responses)

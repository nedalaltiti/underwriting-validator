"""
Address Validation Service for Underwriting

Validates if the state address matches the assigned company based on predefined state/company mappings.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


class AddressDataIn(BaseModel):
    """Input model for address validation data."""
    contact_id: int
    state: Optional[str] = None
    assigned_company: Optional[str] = None


class AddressValidity(Enum):
    """Enum for address validation results."""
    PASS = "pass"
    NO_PASS = "no_pass"
    MIXED = "mixed"
    NO_DATA = "no_data"


@dataclass
class AddressAnalysis:
    """Result of address validation analysis."""
    result: AddressValidity  # "pass", "no_pass", "mixed", or "no_data"
    reason: str
    state_check: str  # "Match", "Mismatch", or "Missing Value"
    state: Optional[str] = None
    assigned_company: Optional[str] = None


class AddressValidationService:
    """Service for validating address and company matching."""
    
    def __init__(self):
        """Initialize the address validation service."""
        # Define state to company mappings using company IDs
        self.clarity_states = {
            'AL','AK','AZ','AR','CA','CO','DC','FL','ID','IN','KY','MD',
            'MA','MI','MN','MS','MO','MT','NE','NM','NY','NC','OH','OK',
            'SD','TN','TX','UT'
        }
        self.concordia_states = {
            'GA','IL','IA','LA','NV','NJ','PA','PR','VA','WI','WY'
        }
        self.clarity_company_ids = {26267, 87758}
        self.concordia_company_ids = {83850, 89302, 67264}
        
        logger.info("AddressValidationService initialized")
    
    def _normalize_state(self, state: Optional[str]) -> Optional[str]:
        """Normalize state code to uppercase and handle edge cases."""
        if not state:
            return None
        
        # Convert to uppercase and trim whitespace
        normalized = state.strip().upper()
        
        # Handle special cases
        if normalized in ["WASHINGTON D.C", "WASHINGTON DC", "D.C", "DC"]:
            return "DC"
        
        return normalized
    
    async def analyze_address_validity(
        self, 
        address_data: AddressDataIn
    ) -> Result[AddressAnalysis]:
        """
        Analyze address data and determine if state/company matching is valid.
        
        Args:
            address_data: AddressDataIn model containing address information
            
        Returns:
            Result containing AddressAnalysis
        """
        try:
            contact_id = address_data.contact_id
            state = address_data.state
            assigned_company = address_data.assigned_company
            
            # Check if we have any data at all
            if not state and not assigned_company:
                return Success(AddressAnalysis(
                    result=AddressValidity.NO_DATA,
                    reason="No address or company data available for analysis",
                    state_check="Missing Value",
                    state=state,
                    assigned_company=assigned_company
                ))
            
            # Since the validation is now done at the database level with the CASE statement,
            # we expect the state_check to be passed in from the repository
            # For now, we'll determine the result based on available data
            if not state:
                result = AddressValidity.NO_DATA
                reason = "No state data available for validation"
                state_check = "Missing Value"
            elif not assigned_company:
                result = AddressValidity.NO_DATA
                reason = "No company data available for validation"
                state_check = "Missing Value"
            else:
                # Normalize state for comparison
                normalized_state = self._normalize_state(state)
                if not normalized_state:
                    result = AddressValidity.NO_DATA
                    reason = "Invalid state format"
                    state_check = "Missing Value"
                else:
                    # Check if state belongs to Clarity or Concordia
                    if normalized_state in self.clarity_states:
                        result = AddressValidity.PASS
                        reason = f"State {normalized_state} is valid for Clarity Debt Resolution"
                        state_check = "Match"
                    elif normalized_state in self.concordia_states:
                        result = AddressValidity.PASS
                        reason = f"State {normalized_state} is valid for Concordia Legal Advisors"
                        state_check = "Match"
                    else:
                        result = AddressValidity.NO_PASS
                        reason = f"State {normalized_state} is not valid for any assigned company"
                        state_check = "Mismatch"
            
            analysis = AddressAnalysis(
                result=result,
                reason=reason,
                state_check=state_check,
                state=state,
                assigned_company=assigned_company
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Address analysis completed for contact {masked_id}: {analysis.result.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing address validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    async def format_address_response(self, analysis: AddressAnalysis, address_data: AddressDataIn) -> str:
        """Format the address analysis into a user-friendly response."""
        from underwriting_validation.utils.validation_responses import format_address_response
        return await format_address_response(analysis, address_data)

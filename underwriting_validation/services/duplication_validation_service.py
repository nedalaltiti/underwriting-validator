"""
Duplication Validation Service for Underwriting

This service handles duplication validation analysis by checking if a contact's SSN or phone number
already exists in the system under certain status conditions.
"""

import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
from underwriting_validation.infrastructure.duplication_repository import DuplicationRepository
from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class DuplicationDataIn(BaseModel):
    """Input model for duplication validation data."""
    contact_id: int
    ssn: Optional[str] = None
    phone: Optional[str] = None

class DuplicationAnalysis(BaseModel):
    """Analysis result for duplication validation."""
    contact_id: int
    has_duplicates: bool
    ssn_duplicate_count: int
    phone_duplicate_count: int
    ssn_duplicates: list
    phone_duplicates: list
    result: str
    reason: str

class DuplicationValidationService:
    """Service for performing duplication validation analysis."""
    
    def __init__(self, repository: DuplicationRepository):
        self.repository = repository
        logger.info("DuplicationValidationService initialized")
    
    async def analyze_duplication_validity(self, data: DuplicationDataIn) -> Result[DuplicationAnalysis]:
        """
        Analyze duplication validity for a contact.
        
        Args:
            data: DuplicationDataIn containing contact information
            
        Returns:
            Result containing DuplicationAnalysis or error message
        """
        try:
            masked_id = mask_contact_id(data.contact_id)
            logger.info(f"Analyzing duplication validity for contact {masked_id}")
            
            # Check for duplication using the repository
            duplication_data = await self.repository.check_contact_duplication(data.contact_id)
            
            if duplication_data.get("error"):
                logger.warning(f"Error in duplication check for contact {masked_id}: {duplication_data['error']}")
                return Error(f"Duplication check failed: {duplication_data['error']}")
            
            has_duplicates = duplication_data.get("has_duplicates", False)
            ssn_duplicate_count = duplication_data.get("ssn_duplicate_count", 0)
            phone_duplicate_count = duplication_data.get("phone_duplicate_count", 0)
            ssn_duplicates = duplication_data.get("ssn_duplicates", [])
            phone_duplicates = duplication_data.get("phone_duplicates", [])
            
            # Determine the result and reason
            if has_duplicates:
                result = "duplicate_found"
                if ssn_duplicate_count > 0 and phone_duplicate_count > 0:
                    reason = f"Contact has {ssn_duplicate_count} SSN duplicate(s) and {phone_duplicate_count} phone duplicate(s) in the system"
                elif ssn_duplicate_count > 0:
                    reason = f"Contact has {ssn_duplicate_count} SSN duplicate(s) in the system"
                else:
                    reason = f"Contact has {phone_duplicate_count} phone duplicate(s) in the system"
            else:
                result = "no_duplicates"
                reason = "No duplicates found for this contact's SSN or phone number"
            
            analysis = DuplicationAnalysis(
                contact_id=data.contact_id,
                has_duplicates=has_duplicates,
                ssn_duplicate_count=ssn_duplicate_count,
                phone_duplicate_count=phone_duplicate_count,
                ssn_duplicates=ssn_duplicates,
                phone_duplicates=phone_duplicates,
                result=result,
                reason=reason
            )
            
            logger.info(f"Duplication analysis for contact {masked_id}: result={result}, duplicates_found={has_duplicates}")
            return Success(analysis)
            
        except Exception as e:
            masked_id = mask_contact_id(data.contact_id)
            logger.error(f"Error analyzing duplication validity for contact {masked_id}: {e}")
            return Error(f"Duplication analysis failed: {str(e)}")
    
    async def analyze_duplication_validity_from_dict(self, data: Dict[str, Any]) -> Result[DuplicationAnalysis]:
        """
        Analyze duplication validity from a dictionary.
        
        Args:
            data: Dictionary containing duplication data
            
        Returns:
            Result containing DuplicationAnalysis or error message
        """
        try:
            # Convert dictionary to Pydantic model
            duplication_data = DuplicationDataIn(
                contact_id=data.get("contact_id"),
                ssn=data.get("ssn"),
                phone=data.get("phone")
            )
            
            return await self.analyze_duplication_validity(duplication_data)
            
        except Exception as e:
            logger.error(f"Error converting duplication data to model: {e}")
            return Error(f"Data conversion failed: {str(e)}")

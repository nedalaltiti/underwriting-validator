"""
Contact Service for Underwriting (Refactored)

A streamlined service that uses utility modules for contact operations.
This service orchestrates contact validation, analysis, and response formatting.
"""

import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from underwriting_validation.infrastructure.contact_repository import ContactRepository
from underwriting_validation.services.hardship_validation_service import HardshipValidationService
from underwriting_validation.services.budget_validation_service import BudgetValidationService
from underwriting_validation.services.address_validation_service import AddressValidationService

# Import utility modules
from underwriting_validation.utils.contact_validation import (
    InvalidContactIDError, 
    ContactNotFoundError,
    check_contact_eligibility
)
from underwriting_validation.utils.contact_data import ContactDataCache
from underwriting_validation.utils.contact_analysis import (
    analyze_contact_hardship,
    analyze_contact_budget,
    analyze_contact_address
)
from underwriting_validation.utils.contact_response import (
    format_contact_response,
    format_budget_response,
    format_address_response
)

logger = logging.getLogger(__name__)

class ContactQueryRequest(BaseModel):
    """Request model for contact queries with validation."""
    contact_id: int = Field(ge=1, description="Contact ID must be a positive integer")


class ContactService:
    """Streamlined service for managing contact information and validation."""
    
    def __init__(self, hardship_service: HardshipValidationService, repository: ContactRepository):
        self.hardship_service = hardship_service
        self.budget_service = BudgetValidationService()
        self.address_service = AddressValidationService()
        self.repository = repository
        
        logger.info("ContactService initialized with utility modules")
    
    async def analyze_contact_hardship(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """
        Analyze contact hardship using utility functions.
        
        Args:
            contact_id: The ID of the contact to analyze
            
        Returns:
            Dictionary containing hardship analysis results or None if contact not found
        """
        cache = ContactDataCache()
        return await analyze_contact_hardship(
            self.hardship_service, 
            self.repository, 
            cache, 
            contact_id
        )
    
    async def get_contact_budget_analysis(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """
        Analyze contact budget using utility functions.
        
        Args:
            contact_id: The ID of the contact to analyze
            
        Returns:
            Dictionary containing budget analysis results or None if contact not found
        """
        cache = ContactDataCache()
        return await analyze_contact_budget(
            self.budget_service, 
            self.repository, 
            cache, 
            contact_id
        )
    
    async def analyze_contact_address(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """
        Analyze contact address using utility functions.
        
        Args:
            contact_id: The ID of the contact to analyze
            
        Returns:
            Dictionary containing address analysis results or None if contact not found
        """
        cache = ContactDataCache()
        return await analyze_contact_address(
            self.address_service, 
            self.repository, 
            cache, 
            contact_id
        )
    
    async def check_contact_eligibility(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """
        Check contact eligibility using utility functions.
        
        Args:
            contact_id: The ID of the contact to check
            
        Returns:
            Dictionary containing eligibility information or None if not eligible
        """
        return await check_contact_eligibility(self.repository, contact_id)
    
    # Response formatting methods
    def format_contact_response(self, contact: Dict[str, Any]) -> str:
        """Format hardship analysis results."""
        return format_contact_response(contact)
    
    def format_budget_response(self, budget: Dict[str, Any]) -> str:
        """Format budget analysis results."""
        return format_budget_response(budget)
    
    def format_address_response(self, address: Dict[str, Any]) -> str:
        """Format address analysis results."""
        return format_address_response(address)

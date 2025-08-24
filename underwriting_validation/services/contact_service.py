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
from underwriting_validation.services.credit_score_validation_service import CreditScoreValidationService

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
        self.credit_score_service = CreditScoreValidationService()
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
    
    async def analyze_contact_credit_score(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """
        Analyze contact credit score using utility functions.
        
        Args:
            contact_id: The ID of the contact to analyze
            
        Returns:
            Dictionary containing credit score analysis results or None if contact not found
        """
        try:
            # Get credit score data from repository
            credit_score_data = await self.repository.fetch_contact_with_credit_score_data(contact_id)
            
            if not credit_score_data:
                return None
            
            # Create input model for validation service
            from underwriting_validation.services.credit_score_validation_service import CreditScoreDataIn
            credit_score_input = CreditScoreDataIn(
                contact_id=credit_score_data["contact_id"],
                equifax=credit_score_data["equifax"],
                experian=credit_score_data["experian"],
                transunion=credit_score_data["transunion"],
                credit_score=credit_score_data["credit_score"],
                has_credit_data=credit_score_data["has_credit_data"]
            )
            
            # Analyze credit score validity
            analysis_result = await self.credit_score_service.analyze_credit_score_validity(credit_score_input)
            
            if analysis_result.is_success():
                analysis = analysis_result.value
                return {
                    "contact_id": credit_score_data["contact_id"],
                    "acctid": credit_score_data["acctid"],
                    "equifax": credit_score_data["equifax"],
                    "experian": credit_score_data["experian"],
                    "transunion": credit_score_data["transunion"],
                    "credit_score": credit_score_data["credit_score"],
                    "has_credit_data": credit_score_data["has_credit_data"],
                    "credit_score_status": credit_score_data["credit_score_status"],
                    "credit_score_message": credit_score_data["credit_score_message"],
                    "analysis": {
                        "result": analysis.result.value,
                        "reason": analysis.reason,
                        "credit_score_status": analysis.credit_score_status
                    }
                }
            else:
                logger.error(f"Credit score analysis failed: {analysis_result.error}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing contact credit score: {e}")
            return None
    
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
    async def format_contact_response(self, contact: Dict[str, Any]) -> str:
        """Format hardship analysis results."""
        return await format_contact_response(contact)
    
    async def format_budget_response(self, budget: Dict[str, Any]) -> str:
        """Format budget analysis results."""
        return await format_budget_response(budget)
    
    async def format_address_response(self, address: Dict[str, Any]) -> str:
        """Format address analysis results."""
        return await format_address_response(address)
    
    async def format_credit_score_response(self, credit_score: Dict[str, Any]) -> str:
        """Format credit score analysis results."""
        from underwriting_validation.utils.credit_score_responses import format_credit_score_response
        
        # Extract analysis and credit_score_data from the credit_score dictionary
        analysis = credit_score.get('analysis', {})
        credit_score_data = {
            'contact_id': credit_score.get('contact_id'),
            'equifax': credit_score.get('equifax'),
            'experian': credit_score.get('experian'),
            'transunion': credit_score.get('transunion'),
            'credit_score': credit_score.get('credit_score'),
            'has_credit_data': credit_score.get('has_credit_data')
        }
        
        # Create mock objects for the new format
        class MockAnalysis:
            def __init__(self, data):
                self.result = type('MockResult', (), {'value': data.get('result', 'unknown')})()
                self.reason = data.get('reason', '')
                self.credit_score_status = data.get('credit_score_status', 'unknown')
                self.equifax = credit_score.get('equifax', 0)
                self.experian = credit_score.get('experian', 0)
                self.transunion = credit_score.get('transunion', 0)
                self.credit_score = credit_score.get('credit_score', 0)
                self.has_credit_data = credit_score.get('has_credit_data', False)
        
        class MockCreditScoreData:
            def __init__(self, data):
                self.contact_id = data.get('contact_id')
        
        mock_analysis = MockAnalysis(analysis)
        mock_credit_score_data = MockCreditScoreData(credit_score_data)
        
        return await format_credit_score_response(mock_analysis, mock_credit_score_data)
    
 
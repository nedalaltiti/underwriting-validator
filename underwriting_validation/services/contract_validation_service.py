"""
Contract Validation Service for Underwriting

This service provides a unified interface for contract validation by delegating to
specialized modules for data models, analysis, and orchestration.
"""

import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

# Import the new modular components
from underwriting_validation.services.contract_models import ContractDataIn, ContractAnalysis
from underwriting_validation.services.contract_validation_orchestrator import ContractValidationOrchestrator

logger = logging.getLogger(__name__)


class ContractValidationService:
    """Main service for contract validation operations."""
    
    def __init__(self):
        """Initialize the contract validation service."""
        self.orchestrator = ContractValidationOrchestrator()
        logger.info("ContractValidationService initialized")
    
    async def analyze_contract_validity(
        self, 
        contract_data: ContractDataIn
    ) -> Result[ContractAnalysis]:
        """
        Analyze contract data and determine validity.
        
        Args:
            contract_data: ContractDataIn model containing contract information
            
        Returns:
            Result containing ContractAnalysis
        """
        try:
            contact_id = contract_data.contact_id
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Starting contract validation for contact {masked_id}")
            
            # Delegate to orchestrator
            result = await self.orchestrator.execute_validations(contract_data)
            
            if result.is_error():
                logger.error(f"Contract validation failed for contact {masked_id}: {result.error}")
                return result
            
            analysis = result.value
            logger.info(f"Contract validation completed for contact {masked_id}: {analysis.result.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error in contract validation: {e}")
            return Error(f"Contract validation failed: {str(e)}")
    
    def format_contract_response(self, analysis: ContractAnalysis, contract_data: ContractDataIn) -> str:
        """Format the contract analysis into a user-friendly response."""
        from underwriting_validation.utils.contract_responses import format_contract_response
        return format_contract_response(analysis, contract_data)

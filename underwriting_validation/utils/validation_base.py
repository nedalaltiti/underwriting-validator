"""
Base classes and utilities for validation services.

This module provides base classes that eliminate DRY violations across
validation services while maintaining the specialized architecture.
"""

import logging
from typing import Any, Callable, TypeVar, Optional, Dict
from abc import ABC, abstractmethod

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

T = TypeVar('T')

class ValidationServiceBase(ABC):
    """
    Base class for all validation services.
    
    Eliminates DRY violations by providing:
    - Standardized initialization
    - Common error handling patterns
    - Consistent logging
    - PII-safe contact ID handling
    """
    
    def __init__(self, service_name: str):
        """
        Initialize validation service with standardized logging.
        
        Args:
            service_name: Name of the service for logging purposes
        """
        self.service_name = service_name
        self.logger = logging.getLogger(f"{__name__}.{service_name}")
        self.logger.info(f"{service_name} initialized")
    
    def safe_execute(
        self, 
        operation_name: str, 
        contact_id: int, 
        operation: Callable[[], T]
    ) -> Result[T]:
        """
        Execute an operation with standardized error handling and logging.
        
        This method eliminates the repeated try/catch pattern found across
        all validation services.
        
        Args:
            operation_name: Name of the operation for logging
            contact_id: Contact ID for PII-safe logging
            operation: Function to execute safely
            
        Returns:
            Result containing the operation result or error
        """
        try:
            masked_id = mask_contact_id(contact_id)
            self.logger.debug(f"Starting {operation_name} for contact {masked_id}")
            
            result = operation()
            
            self.logger.info(f"{operation_name} completed successfully for contact {masked_id}")
            return Success(result)
            
        except Exception as e:
            masked_id = mask_contact_id(contact_id)
            error_msg = f"Error in {operation_name} for contact {masked_id}: {str(e)}"
            self.logger.error(error_msg)
            return Error(f"{operation_name} failed: {str(e)}")
    
    def log_analysis_completion(self, contact_id: int, result_summary: str):
        """
        Log analysis completion with PII-safe contact ID.
        
        Args:
            contact_id: Contact ID to log
            result_summary: Summary of the analysis result
        """
        masked_id = mask_contact_id(contact_id)
        self.logger.info(f"Analysis completed for contact {masked_id}: {result_summary}")
    
    def log_analysis_error(self, contact_id: int, error: Exception):
        """
        Log analysis error with PII-safe contact ID.
        
        Args:
            contact_id: Contact ID to log
            error: Exception that occurred
        """
        masked_id = mask_contact_id(contact_id)
        self.logger.error(f"Error analyzing {self.get_validation_type()} validity for contact {masked_id}: {error}")
    
    @abstractmethod
    def get_validation_type(self) -> str:
        """
        Get the validation type name for this service.
        
        Returns:
            String identifying the validation type (e.g., 'IP', 'email', 'signature')
        """
        pass
    
    def create_missing_data_result(self, data_type: str) -> Dict[str, Any]:
        """
        Create standardized result for missing data scenarios.
        
        Args:
            data_type: Type of data that is missing
            
        Returns:
            Standardized missing data result
        """
        return {
            "result": "no_data",
            "reason": f"No {data_type} data available for analysis",
            "confidence": 0.0
        }
    
    def create_validation_result(
        self, 
        result_type: str, 
        reason: str, 
        confidence: float = 1.0,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create standardized validation result.
        
        Args:
            result_type: Type of result ('pass', 'no_pass', 'mixed', 'no_data')
            reason: Human-readable reason for the result
            confidence: Confidence level (0.0-1.0)
            additional_data: Additional data to include in result
            
        Returns:
            Standardized validation result dictionary
        """
        result = {
            "result": result_type,
            "reason": reason,
            "confidence": confidence
        }
        
        if additional_data:
            result.update(additional_data)
        
        return result


class ContractValidationServiceBase(ValidationServiceBase):
    """
    Base class specifically for contract validation services.
    
    Provides common patterns used across all contract validation services.
    """
    
    def __init__(self, service_name: str):
        super().__init__(service_name)
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> Optional[str]:
        """
        Validate that required fields are present and non-empty.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Returns:
            None if valid, error message if invalid
        """
        missing_fields = []
        for field in required_fields:
            value = data.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ''):
                missing_fields.append(field)
        
        if missing_fields:
            return f"Missing required fields: {', '.join(missing_fields)}"
        
        return None
    
    def normalize_string_field(self, value: Optional[str]) -> Optional[str]:
        """
        Normalize string field by trimming whitespace and handling empty strings.
        
        Args:
            value: String value to normalize
            
        Returns:
            Normalized string or None if empty
        """
        if value is None:
            return None
        
        normalized = value.strip()
        return normalized if normalized else None
    
    def format_validation_response(self, result_enum, success_msg: str, failure_msg: str, missing_msg: str) -> str:
        """
        Format validation response based on result enum.
        
        Args:
            result_enum: Validation result enum
            success_msg: Message for successful validation
            failure_msg: Message for failed validation  
            missing_msg: Message for missing data
            
        Returns:
            Formatted response string
        """
        if hasattr(result_enum, 'value'):
            result_value = result_enum.value
        else:
            result_value = str(result_enum)
        
        if result_value == "Match" or result_value == "Valid":
            return f"✅ {success_msg}"
        elif result_value == "Mismatch" or result_value == "Invalid":
            return f"❌ {failure_msg}"
        else:
            return f"⚠️ {missing_msg}"


class AnalysisServiceBase(ValidationServiceBase):
    """
    Base class for services that perform data analysis (like hardship, budget).
    
    Provides common patterns for analysis services that work with LLM or
    complex business logic.
    """
    
    def __init__(self, service_name: str):
        super().__init__(service_name)
    
    def calculate_confidence_score(self, data_quality_factors: Dict[str, float]) -> float:
        """
        Calculate confidence score based on data quality factors.
        
        Args:
            data_quality_factors: Dictionary of factor_name -> weight (0.0-1.0)
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not data_quality_factors:
            return 0.0
        
        total_weight = sum(data_quality_factors.values())
        if total_weight == 0:
            return 0.0
        
        # Weighted average
        return min(1.0, total_weight / len(data_quality_factors))
    
    def format_currency(self, amount: Optional[float]) -> str:
        """
        Format currency amount for display.
        
        Args:
            amount: Amount to format
            
        Returns:
            Formatted currency string
        """
        if amount is None:
            return "N/A"
        
        return f"${amount:,.2f}"
    
    def format_percentage(self, value: float) -> str:
        """
        Format percentage for display.
        
        Args:
            value: Percentage value (0.0-1.0)
            
        Returns:
            Formatted percentage string
        """
        return f"{value * 100:.1f}%"
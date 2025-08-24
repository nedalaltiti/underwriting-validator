"""
Base classes for services layer.
"""

from underwriting_validation.utils.validation_base import (
    ValidationServiceBase, 
    ContractValidationServiceBase, 
    AnalysisServiceBase
)

__all__ = [
    'ValidationServiceBase',
    'ContractValidationServiceBase', 
    'AnalysisServiceBase'
]
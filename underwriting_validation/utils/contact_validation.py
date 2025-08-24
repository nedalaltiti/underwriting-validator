"""
Contact Validation Utilities

This module provides validation utilities for contact operations including:
- Contact ID validation
- Eligibility checking
- Validation error handling
"""

import logging
from typing import Optional, Dict, Any
from underwriting_validation.infrastructure.contact_repository import ContactRepository
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class InvalidContactIDError(ValueError):
    """Raised when a contact ID is invalid or out of range."""
    pass

class ContactNotFoundError(ValueError):
    """Raised when a contact ID is valid but not found in database."""
    pass


def validate_contact_id(contact_id: int) -> bool:
    """
    Validate contact ID format and range.
    
    Args:
        contact_id: The contact ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Basic validation: must be a positive integer
        if not isinstance(contact_id, int) or contact_id <= 0:
            return False
        
        # Check for reasonable bounds (up to 11 digits to handle incremental IDs)
        if contact_id > 10**11:  # 11 digits max
            return False
        
        return True
    except (ValueError, TypeError):
        return False


async def check_contact_eligibility(repository: ContactRepository, contact_id: int) -> Optional[Dict[str, Any]]:
    """
    Check if a contact is eligible for validation process.
    
    Args:
        repository: Contact repository instance
        contact_id: The ID of the contact to check
        
    Returns:
        Dictionary containing eligibility information or None if not eligible
    """
    # Validate contact ID format first
    if not validate_contact_id(contact_id):
        raise InvalidContactIDError(f"Contact ID {contact_id} is out of range (must be 1-11 digits)")
    
    try:
        eligibility_data = await repository.check_contact_eligibility(contact_id)
        if not eligibility_data:
            return None  # Contact is not eligible
        return eligibility_data
    except Exception as e:
        masked_id = mask_contact_id(contact_id)
        logger.error(f"Error checking contact eligibility for {masked_id}: {e}")
        return None


def validate_and_raise_if_invalid(contact_id: int) -> None:
    """
    Validate contact ID and raise appropriate exception if invalid.
    
    Args:
        contact_id: The contact ID to validate
        
    Raises:
        InvalidContactIDError: If contact ID is invalid
    """
    if not validate_contact_id(contact_id):
        raise InvalidContactIDError(f"Contact ID {contact_id} is out of range (must be 1-11 digits)")

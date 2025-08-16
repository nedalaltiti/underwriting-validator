"""
Contact Data Utilities

This module provides utilities for contact data operations including:
- Data fetching from repository
- Caching mechanisms
- Data availability checks
"""

import logging
from typing import Optional, Dict, Any
from underwriting_validation.infrastructure.contact_repository import ContactRepository
from underwriting_validation.utils.pii_filter import mask_contact_id
from .contact_validation import validate_and_raise_if_invalid, ContactNotFoundError

logger = logging.getLogger(__name__)


class ContactDataCache:
    """Simple per-request cache for contact data to avoid duplicate queries."""
    
    def __init__(self):
        self._hardship_cache = {}
        self._budget_cache = {}
        self._address_cache = {}
    
    def get_hardship_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Get hardship data from cache."""
        return self._hardship_cache.get(contact_id)
    
    def set_hardship_data(self, contact_id: int, data: Optional[Dict[str, Any]]) -> None:
        """Set hardship data in cache."""
        self._hardship_cache[contact_id] = data
    
    def get_budget_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Get budget data from cache."""
        return self._budget_cache.get(contact_id)
    
    def set_budget_data(self, contact_id: int, data: Optional[Dict[str, Any]]) -> None:
        """Set budget data in cache."""
        self._budget_cache[contact_id] = data
    
    def get_address_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Get address data from cache."""
        return self._address_cache.get(contact_id)
    
    def set_address_data(self, contact_id: int, data: Optional[Dict[str, Any]]) -> None:
        """Set address data in cache."""
        self._address_cache[contact_id] = data
    
    def clear(self) -> None:
        """Clear all cached data."""
        self._hardship_cache.clear()
        self._budget_cache.clear()
        self._address_cache.clear()


async def get_or_fetch_hardship_data(
    repository: ContactRepository, 
    cache: ContactDataCache, 
    contact_id: int
) -> Optional[Dict[str, Any]]:
    """
    Get hardship data from cache or fetch from database.
    
    Args:
        repository: Contact repository instance
        cache: Data cache instance
        contact_id: The contact ID to fetch hardship data for
        
    Returns:
        Hardship data dictionary or None if not found
    """
    # Check cache first
    masked_id = mask_contact_id(contact_id)
    cached_data = cache.get_hardship_data(contact_id)
    if cached_data is not None:
        logger.debug(f"Using cached hardship data for contact {masked_id}")
        return cached_data
    
    # Fetch from database
    logger.debug(f"Fetching hardship data for contact {masked_id} from database")
    data = await repository.fetch_contact_with_hardship_data(contact_id)
    
    # Cache the result (even if None, to avoid repeated DB calls)
    cache.set_hardship_data(contact_id, data)
    return data


async def get_contact_with_budget_data(
    repository: ContactRepository, 
    cache: ContactDataCache, 
    contact_id: int
) -> Optional[Dict[str, Any]]:
    """
    Retrieve contact information with budget data using repository.
    
    Args:
        repository: Contact repository instance
        cache: Data cache instance
        contact_id: The ID of the contact to retrieve
        
    Returns:
        Dictionary containing contact and budget information or None if not found
    """
    validate_and_raise_if_invalid(contact_id)
    
    # Check cache first
    cached_data = cache.get_budget_data(contact_id)
    if cached_data is not None:
        return cached_data
    
    try:
        data = await repository.fetch_contact_with_budget_data(contact_id)
        if not data:
            raise ContactNotFoundError(f"Contact {contact_id} not found in database")
        
        cache.set_budget_data(contact_id, data)
        return data
    except Exception as e:
        masked_id = mask_contact_id(contact_id)
        logger.error(f"Error retrieving contact budget data for {masked_id}: {e}")
        raise ContactNotFoundError(f"Contact {contact_id} not found in database")


async def get_contact_with_hardship_data(
    repository: ContactRepository, 
    cache: ContactDataCache, 
    contact_id: int
) -> Optional[Dict[str, Any]]:
    """
    Retrieve contact information with hardship data using repository.
    
    Args:
        repository: Contact repository instance
        cache: Data cache instance
        contact_id: The ID of the contact to retrieve
        
    Returns:
        Dictionary containing contact and hardship information or None if not found
    """
    validate_and_raise_if_invalid(contact_id)
    
    try:
        data = await get_or_fetch_hardship_data(repository, cache, contact_id)
        if not data:
            raise ContactNotFoundError(f"Contact {contact_id} not found in database")
        return data
    except Exception as e:
        masked_id = mask_contact_id(contact_id)
        logger.error(f"Error retrieving contact hardship data for {masked_id}: {e}")
        raise ContactNotFoundError(f"Contact {contact_id} not found in database")


async def get_contact_with_address_data(
    repository: ContactRepository, 
    cache: ContactDataCache, 
    contact_id: int
) -> Optional[Dict[str, Any]]:
    """
    Retrieve contact information with address data using repository.
    
    Args:
        repository: Contact repository instance
        cache: Data cache instance
        contact_id: The ID of the contact to retrieve
        
    Returns:
        Dictionary containing contact and address information or None if not found
    """
    validate_and_raise_if_invalid(contact_id)
    
    # Check cache first
    cached_data = cache.get_address_data(contact_id)
    if cached_data is not None:
        return cached_data
    
    try:
        data = await repository.fetch_contact_with_address_data(contact_id)
        if not data:
            raise ContactNotFoundError(f"Contact {contact_id} not found in database")
        
        cache.set_address_data(contact_id, data)
        return data
    except Exception as e:
        masked_id = mask_contact_id(contact_id)
        logger.error(f"Error retrieving contact address data for {masked_id}: {e}")
        raise ContactNotFoundError(f"Contact {contact_id} not found in database")


def has_hardship_data(hardship_data: Optional[Dict[str, Any]]) -> bool:
    """Check if hardship data contains meaningful information."""
    if not hardship_data:
        return False
    return any([
        hardship_data.get('financial_hardship'),
        hardship_data.get('hardship_description')
    ])


def has_budget_data(budget_data: Optional[Dict[str, Any]]) -> bool:
    """Check if budget data contains meaningful information."""
    if not budget_data:
        return False
    return any([
        budget_data.get('total_net_income', 0) > 0,
        budget_data.get('total_expenses', 0) > 0
    ])


def has_address_data(address_data: Optional[Dict[str, Any]]) -> bool:
    """Check if address data contains meaningful information."""
    if not address_data:
        return False
    return any([
        address_data.get('state'),
        address_data.get('assigned_company')
    ])

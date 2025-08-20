"""
Phone number cleaning utilities.

This module contains functions to clean phone numbers by removing special characters
and formatting them consistently.
"""

import re
from typing import Optional


def clean_phone_number(phone: Optional[str]) -> Optional[str]:
    """
    Clean a phone number by removing all special characters except digits.
    
    Args:
        phone: The phone number string to clean
        
    Returns:
        Cleaned phone number with only digits, or None if input is None/empty
    """
    if not phone:
        return None
    
    # Remove all non-digit characters
    cleaned = re.sub(r'[^\d]', '', str(phone))
    
    # Return None if empty after cleaning
    return cleaned if cleaned else None


def format_phone_number(phone: Optional[str], format_type: str = "clean") -> Optional[str]:
    """
    Format a phone number according to specified format.
    
    Args:
        phone: The phone number to format
        format_type: Format type - "clean" (digits only), "formatted" (with dashes)
        
    Returns:
        Formatted phone number or None if input is None/empty
    """
    if not phone:
        return None
    
    # First clean the phone number
    cleaned = clean_phone_number(phone)
    if not cleaned:
        return None
    
    if format_type == "formatted":
        # Format as XXX-XXX-XXXX
        if len(cleaned) == 10:
            return f"{cleaned[:3]}-{cleaned[3:6]}-{cleaned[6:]}"
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            # Remove country code and format
            return f"{cleaned[1:4]}-{cleaned[4:7]}-{cleaned[7:]}"
        else:
            # Return cleaned if can't format
            return cleaned
    
    # Default to clean format (digits only)
    return cleaned

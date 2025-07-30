"""
PII Filter for logging sensitive data.

This module provides logging filters to mask Personally Identifiable Information (PII)
such as contact IDs in log messages.
"""

import re
import logging
from typing import Optional


class PIIFilter(logging.Filter):
    """Filter to mask PII data in log messages."""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
    
    def filter(self, record):
        """Filter and mask PII data in log messages."""
        if hasattr(record, 'msg'):
            # Mask contact IDs in logs
            record.msg = re.sub(
                r'contact[_\s]+(?:id[_\s]+)?(\d{4,})', 
                lambda m: f'contact_id_***{m.group(1)[-3:]}', 
                str(record.msg)
            )
            
            # Also mask standalone contact IDs (without "contact" prefix)
            record.msg = re.sub(
                r'\b(\d{4,})\b(?=.*contact)',
                lambda m: f'***{m.group(1)[-3:]}',
                str(record.msg)
            )
            
            # Mask contact IDs in args if present
            if hasattr(record, 'args') and record.args:
                new_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        # Apply same masking to string arguments
                        masked_arg = re.sub(
                            r'contact[_\s]+(?:id[_\s]+)?(\d{4,})', 
                            lambda m: f'contact_id_***{m.group(1)[-3:]}', 
                            arg
                        )
                        masked_arg = re.sub(
                            r'\b(\d{4,})\b(?=.*contact)',
                            lambda m: f'***{m.group(1)[-3:]}',
                            masked_arg
                        )
                        new_args.append(masked_arg)
                    else:
                        new_args.append(arg)
                record.args = tuple(new_args)
        
        return True


def setup_pii_filtering(logger_name: Optional[str] = None):
    """
    Set up PII filtering for a logger.
    
    Args:
        logger_name: Name of the logger to add PII filtering to.
                    If None, applies to root logger.
    """
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    pii_filter = PIIFilter()
    logger.addFilter(pii_filter)
    return pii_filter


def mask_contact_id(contact_id: int) -> str:
    """
    Mask a contact ID for logging purposes.
    
    Args:
        contact_id: The contact ID to mask
        
    Returns:
        Masked contact ID string
    """
    contact_str = str(contact_id)
    if len(contact_str) <= 3:
        return "***"
    return f"***{contact_str[-3:]}" 
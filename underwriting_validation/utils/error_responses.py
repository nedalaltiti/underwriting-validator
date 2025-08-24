"""
Error and utility response formatters.

This module contains formatting functions for error responses and utility messages.
"""


def format_no_data_response(contact_id: int, validation_type: str = "validation") -> str:
    """Format response when no data is available."""
    return f"Contact {contact_id} does not have {validation_type} data.\nNo {validation_type} information has been recorded for this contact."


def format_error_response(contact_id: int, error_message: str, validation_type: str = "validation") -> str:
    """Format error response."""
    return f"Contact {contact_id} {validation_type} error.\n{error_message}"


def format_invalid_contact_id_response(contact_id: int) -> str:
    """Format response for invalid contact ID."""
    return f"Invalid contact ID: {contact_id}. Please provide a valid contact ID between 1 and 999,999,999,999."

"""
Error and utility response formatters.

This module contains formatting functions for error responses and utility messages.
"""


async def format_no_data_response(contact_id: int, validation_type: str = "validation") -> str:
    """Format a response when no data is available."""
    return f"Contact {contact_id} does not have {validation_type} validation data.\nNo {validation_type} information has been recorded for this contact."


async def format_error_response(contact_id: int, error_message: str, validation_type: str = "validation") -> str:
    """Format an error response."""
    return f"Error processing {validation_type} validation for Contact {contact_id}: {error_message}"


async def format_invalid_contact_id_response(contact_id: int) -> str:
    """Format a response for invalid contact ID."""
    return f"Invalid contact ID: {contact_id}. Please provide a valid contact ID."

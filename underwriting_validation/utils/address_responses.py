"""
Address validation response formatters.

This module contains formatting functions specifically for address validation responses.
"""

from typing import Dict, Any


async def format_address_response(analysis: Any, address_data: Any) -> str:
    """Format address analysis into a user-friendly response."""
    contact_id = address_data.contact_id
    
    # Build organized response
    response_parts = []
    
    # Header with status icon
    if analysis.result.value == "pass":
        response_parts.append(f"Contact {contact_id} has **valid address/company assignment**\n")
    elif analysis.result.value == "mixed":
        response_parts.append(f"Contact {contact_id} has **partial address validation**\n")
    else:
        response_parts.append(f"Contact {contact_id} has **address/company assignment issues**\n")
    
    # Address information section
    response_parts.append("**Address Information:**\n")
    if analysis.state:
        response_parts.append(f"• State: **{analysis.state}**\n")
    if analysis.assigned_company:
        response_parts.append(f"• Assigned Company: **{analysis.assigned_company}**\n")
    
    # Validation results section
    response_parts.append("**Validation Results:**\n")
    response_parts.append(f"• State Check: **{analysis.state_check}**\n")
    response_parts.append(f"• Overall Result: **{analysis.result.value.upper()}**\n")
    response_parts.append(f"• Reason: {analysis.reason}\n")
    
    return "\n".join(response_parts)


async def format_address_analysis_response(address: Dict[str, Any]) -> str:
    """Format address analysis results into a user-friendly response."""
    if not address:
        return "No address data found for that contact ID."
    
    # If there's a formatted response already provided, use it
    if address.get('formatted_response'):
        return address['formatted_response']
    
    # If there's an error, return the error message
    if address.get('error'):
        return f"Error analyzing address data: {address['error']}"
    
    contact_id = address.get('contact_id', 'Unknown')
    
    # Check if there's address data available
    address_data = address.get('address_data', {})
    state = address_data.get('state')
    assigned_company = address_data.get('assigned_company')
    
    has_address_data = any([state, assigned_company])
    
    if not has_address_data:
        return f"Contact {contact_id} does not have address validation data.\nNo address information has been recorded for this contact."
    
    # If there's analysis data, format it with organized structure
    analysis = address.get('analysis')
    if analysis:
        result = analysis.get('result', 'unknown')
        reason = analysis.get('reason', 'No reason provided')
        state_check = analysis.get('state_check', 'Unknown')
        
        # Build organized response
        response_parts = []
        
        # Header with status icon
        if result == 'pass':
            response_parts.append(f"Contact {contact_id} has **valid address/company assignment**")
        elif result == 'mixed':
            response_parts.append(f"Contact {contact_id} has **partial address validation**")
        else:
            response_parts.append(f"Contact {contact_id} has **address/company assignment issues**")
        
        # Address information section
        response_parts.append("")
        response_parts.append("**Address Information:**")
        if state:
            response_parts.append(f"• State: **{state}**")
        if assigned_company:
            response_parts.append(f"• Assigned Company: **{assigned_company}**")
        
        # Validation results section
        response_parts.append("")
        response_parts.append("**Validation Results:**")
        response_parts.append(f"• State Check: **{state_check}**")
        response_parts.append(f"• Overall Result: **{result.upper()}**")
        response_parts.append(f"• Reason: {reason}")
        
        # Summary statement
        if result == 'pass':
            response_parts.append("")
            response_parts.append("**PASS** - Address and company assignments are valid.")
        elif result == 'mixed':
            response_parts.append("")
            response_parts.append("**MIXED** - Some address validation checks passed, manual review may be needed.")
        else:
            response_parts.append("")
            response_parts.append("**NO PASS** - Address or company assignment issues detected.")
        
        return "\n".join(response_parts)
    
    return "Unable to format address analysis results. Please try again."

"""
Duplication validation response formatters.

This module contains formatting functions specifically for duplication validation responses.
"""

from typing import Dict, Any


async def format_duplication_response(analysis: Any, duplication_data: Dict[str, Any]) -> str:
    """Format duplication analysis into a user-friendly response."""
    contact_id = duplication_data.get('contact_id', 'Unknown')
    ssn = duplication_data.get('ssn', '')
    phone = duplication_data.get('phone', '')
    
    # Build organized response
    response_parts = []
    
    # Header with status icon
    if analysis.result == "no_duplicates":
        response_parts.append(f"Contact {contact_id} has **no duplication issues**\n")
    else:
        response_parts.append(f"Contact {contact_id} has **duplication issues detected**\n")
    
    # Duplication information section
    response_parts.append("**Duplication Information:**\n")
    if ssn:
        response_parts.append(f"• SSN: **{ssn}**\n")
    if phone:
        response_parts.append(f"• Phone: **{phone}**\n")
    
    # Duplication results section
    response_parts.append("**Duplication Analysis:**\n")
    response_parts.append(f"• SSN Duplicates: **{analysis.ssn_duplicate_count}**\n")
    response_parts.append(f"• Phone Duplicates: **{analysis.phone_duplicate_count}**\n")
    response_parts.append(f"• Overall Result: **{analysis.result.upper()}**\n")
    response_parts.append(f"• Reason: {analysis.reason}\n")
    
    # Detailed duplicate information if any exist
    if analysis.ssn_duplicates:
        response_parts.append("**SSN Duplicates Found:**\n")
        for i, duplicate in enumerate(analysis.ssn_duplicates, 1):
            duplicate_id = duplicate.get('contact_id', 'Unknown')
            duplicate_acctid = duplicate.get('acctid', 'Unknown')
            response_parts.append(f"• Duplicate {i}: Contact ID {duplicate_id} (Account {duplicate_acctid})\n")
    
    if analysis.phone_duplicates:
        response_parts.append("**Phone Duplicates Found:**\n")
        for i, duplicate in enumerate(analysis.phone_duplicates, 1):
            duplicate_id = duplicate.get('contact_id', 'Unknown')
            duplicate_acctid = duplicate.get('acctid', 'Unknown')
            response_parts.append(f"• Duplicate {i}: Contact ID {duplicate_id} (Account {duplicate_acctid})\n")
    
    return "\n".join(response_parts)


async def format_duplication_analysis_response(duplication: Dict[str, Any]) -> str:
    """Format duplication analysis results into a user-friendly response."""
    if not duplication:
        return "No duplication data found for that contact ID."
    
    # If there's a formatted response already provided, use it
    if duplication.get('formatted_response'):
        return duplication['formatted_response']
    
    # If there's an error, return the error message
    if duplication.get('error'):
        return f"Error analyzing duplication data: {duplication['error']}"
    
    contact_id = duplication.get('contact_id', 'Unknown')
    
    # Check if there's duplication data available
    duplication_data = duplication.get('duplication_data', {})
    ssn = duplication_data.get('ssn')
    phone = duplication_data.get('phone')
    
    has_duplication_data = any([ssn, phone])
    
    if not has_duplication_data:
        return f"Contact {contact_id} does not have duplication validation data.\nNo SSN or phone information has been recorded for this contact."
    
    # If there's analysis data, format it with organized structure
    analysis = duplication.get('analysis')
    if analysis:
        result = analysis.get('result', 'unknown')
        reason = analysis.get('reason', 'No reason provided')
        ssn_duplicate_count = analysis.get('ssn_duplicate_count', 0)
        phone_duplicate_count = analysis.get('phone_duplicate_count', 0)
        ssn_duplicates = analysis.get('ssn_duplicates', [])
        phone_duplicates = analysis.get('phone_duplicates', [])
        
        # Build organized response
        response_parts = []
        
        # Header with status icon
        if result == 'no_duplicates':
            response_parts.append(f"Contact {contact_id} has **no duplication issues**")
        else:
            response_parts.append(f"Contact {contact_id} has **duplication issues detected**")
        
        # Duplication information section
        response_parts.append("")
        response_parts.append("**Duplication Information:**")
        if ssn:
            response_parts.append(f"• SSN: **{ssn}**")
        if phone:
            response_parts.append(f"• Phone: **{phone}**")
        
        # Duplication results section
        response_parts.append("")
        response_parts.append("**Duplication Analysis:**")
        response_parts.append(f"• SSN Duplicates: **{ssn_duplicate_count}**")
        response_parts.append(f"• Phone Duplicates: **{phone_duplicate_count}**")
        response_parts.append(f"• Overall Result: **{result.upper()}**")
        response_parts.append(f"• Reason: {reason}")
        
        # Detailed duplicate information if any exist
        if ssn_duplicates:
            response_parts.append("")
            response_parts.append("**SSN Duplicates Found:**")
            for i, duplicate in enumerate(ssn_duplicates, 1):
                duplicate_id = duplicate.get('contact_id', 'Unknown')
                duplicate_acctid = duplicate.get('acctid', 'Unknown')
                response_parts.append(f"• Duplicate {i}: Contact ID {duplicate_id} (Account {duplicate_acctid})")
        
        if phone_duplicates:
            response_parts.append("")
            response_parts.append("**Phone Duplicates Found:**")
            for i, duplicate in enumerate(phone_duplicates, 1):
                duplicate_id = duplicate.get('contact_id', 'Unknown')
                duplicate_acctid = duplicate.get('acctid', 'Unknown')
                response_parts.append(f"• Duplicate {i}: Contact ID {duplicate_id} (Account {duplicate_acctid})")
        
        # Summary statement
        if result == 'no_duplicates':
            response_parts.append("")
            response_parts.append("**PASS** - No duplication issues found for this contact.")
        else:
            response_parts.append("")
            response_parts.append("**NO PASS** - Duplication issues detected. Manual review required.")
        
        return "\n".join(response_parts)
    
    return "Unable to format duplication analysis results. Please try again."


async def format_no_data_response(contact_id: int, validation_type: str = "duplication") -> str:
    """Format a response when no duplication data is available."""
    return f"Contact {contact_id} does not have {validation_type} validation data.\nNo {validation_type} information has been recorded for this contact."

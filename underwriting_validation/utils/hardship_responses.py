"""
Hardship validation response formatters.

This module contains formatting functions specifically for hardship validation responses.
"""

from typing import Dict, Any


def format_hardship_response(analysis: Any, hardship_data: Dict[str, Any]) -> str:
    """Format hardship analysis into a user-friendly response."""
    contact_id = hardship_data.get('contact_id', 'Unknown')
    financial_hardship = hardship_data.get('financial_hardship', '')
    hardship_description = hardship_data.get('hardship_description', '')
    
    # Format confidence as percentage with one decimal place
    confidence_percent = f"{analysis.confidence * 100:.1f}%"
    
    # Build organized response
    response_parts = []
    
    # Header with status icon
    if analysis.result.value == "pass":
        response_parts.append(f"Contact {contact_id} has hardship validation data\n")
    else:
        response_parts.append(f"Contact {contact_id} hardship validation failed\n")
    
    # Hardship information section
    hardship_info = []
    if hardship_description:
        hardship_info.append(f"• Hardship Description: {hardship_description}")
    if financial_hardship:
        hardship_info.append(f"• Financial Hardship Status: {financial_hardship}")
    
    if hardship_info:
        response_parts.append("**Hardship Information:**\n")
        response_parts.extend(hardship_info)
        response_parts.append("")
    
    # Analysis results section
    response_parts.append("**Validation Analysis:**\n")
    response_parts.append(f"• Result: **{analysis.result.value.upper()}**\n")
    response_parts.append(f"• Confidence: **{confidence_percent}**\n")
    response_parts.append(f"• Reason: {analysis.reason}\n")
    
    return "\n".join(response_parts)


def format_contact_response(contact: Dict[str, Any]) -> str:
    """Format contact analysis results into a user-friendly response."""
    if not contact:
        return "No hardship data found for that contact ID."
    
    # If there's a formatted response already provided, use it
    if contact.get('formatted_response'):
        return contact['formatted_response']
    
    # If there's an error, return the error message
    if contact.get('error'):
        return f"Error analyzing hardship data: {contact['error']}"
    
    contact_id = contact.get('contact_id', 'Unknown')
    
    # Check if there's hardship data available
    hardship_data = contact.get('hardship_data', {})
    financial_hardship = hardship_data.get('financial_hardship', '')
    hardship_description = hardship_data.get('hardship_description', '')
    
    has_hardship_data = any([financial_hardship, hardship_description])
    
    if not has_hardship_data:
        return f"Contact {contact_id} does not have hardship validation data.\nNo hardship information has been recorded for this contact."
    
    # If there's analysis data, format it with organized structure
    analysis = contact.get('analysis')
    if analysis:
        result = analysis.get('result', 'unknown')
        confidence = analysis.get('confidence', 0.0)
        reason = analysis.get('reason', 'No reason provided')
        
        # Format confidence as percentage with one decimal place
        confidence_percent = f"{confidence * 100:.1f}%"
        
        # Build organized response
        response_parts = []
        
        # Header with status icon
        if result == 'pass':
            response_parts.append(f"Contact {contact_id} has hardship validation data")
        else:
            response_parts.append(f"Contact {contact_id} hardship validation failed")
        
        # Hardship information section
        hardship_info = []
        if hardship_description:
            hardship_info.append(f"• Hardship Description: {hardship_description}")
        if financial_hardship:
            hardship_info.append(f"• Financial Hardship Status: {financial_hardship}")
        
        if hardship_info:
            response_parts.append("Hardship Information:")
            response_parts.extend(hardship_info)
        
        # Analysis results section
        response_parts.append("")
        response_parts.append("Validation Analysis:")
        response_parts.append(f"• Result: {result.upper()}")
        response_parts.append(f"• Confidence: {confidence_percent}")
        response_parts.append(f"• Reason: {reason}")
        
        # Summary statement
        if result == 'pass':
            response_parts.append("")
            response_parts.append("The hardship validation data is available for this contact.")
        else:
            response_parts.append("")
            response_parts.append("The hardship validation data requires review or additional information.")
        
        return "\n".join(response_parts)
    
    return "Unable to format hardship analysis results. Please try again."

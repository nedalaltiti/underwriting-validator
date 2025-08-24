"""
Credit Score Response Utilities

This module provides formatting functions for credit score validation responses.
"""

from typing import Dict, Any, Optional


async def format_credit_score_response(analysis: Any, credit_score_data: Any) -> str:
    """
    Format credit score analysis into a user-friendly response.
    
    Args:
        analysis: CreditScoreAnalysis object containing validation results
        credit_score_data: CreditScoreDataIn object containing input data
        
    Returns:
        Formatted string response
    """
    contact_id = credit_score_data.contact_id
    
    # Build organized response
    response_parts = []
    
    # Header with status icon
    if analysis.result.value == "pass":
        response_parts.append(f"Contact {contact_id} has **acceptable credit score**\n")
    elif analysis.result.value == "no_data":
        response_parts.append(f"Contact {contact_id} has **missing credit score data**\n")
        response_parts.append("⚠️ **Action Required:** Credit score information must be collected and entered into the system.\n")
    else:
        response_parts.append(f"Contact {contact_id} has **credit score below minimum**\n")
    
    # Credit score information section
    response_parts.append("**Credit Score Information:**\n")
    if analysis.has_credit_data and analysis.credit_score > 0:
        response_parts.append(f"• Equifax: **{analysis.equifax}**\n")
        response_parts.append(f"• Experian: **{analysis.experian}**\n")
        response_parts.append(f"• TransUnion: **{analysis.transunion}**\n")
        response_parts.append(f"• **Total Score: {analysis.credit_score}**\n")
    else:
        response_parts.append("• **No credit score data available**\n")
        response_parts.append("• Equifax: **Not Available**\n")
        response_parts.append("• Experian: **Not Available**\n")
        response_parts.append("• TransUnion: **Not Available**\n")
        response_parts.append("• **Total Score: Not Available**\n")
    
    # Validation results section
    response_parts.append("**Validation Results:**\n")
    response_parts.append(f"• Credit Score Status: **{analysis.credit_score_status.upper()}**\n")
    response_parts.append(f"• Overall Result: **{analysis.result.value.upper()}**\n")
    response_parts.append(f"• Reason: {analysis.reason}\n")
    
    return "\n".join(response_parts)


async def format_credit_score_analysis_response(credit_score: Dict[str, Any]) -> str:
    """
    Format credit score analysis results into a user-friendly response.
    
    Args:
        credit_score: Dictionary containing credit score data and analysis
        
    Returns:
        Formatted string response for detailed analysis
    """
    if not credit_score:
        return "No credit score data found for that contact ID."
    
    # If there's a formatted response already provided, use it
    if credit_score.get('formatted_response'):
        return credit_score['formatted_response']
    
    # If there's an error, return the error message
    if credit_score.get('error'):
        return f"Error analyzing credit score data: {credit_score['error']}"
    
    contact_id = credit_score.get('contact_id', 'Unknown')
    
    # Check if there's credit score data available
    credit_score_data = credit_score.get('credit_score_data', {})
    equifax = credit_score_data.get('equifax', 0)
    experian = credit_score_data.get('experian', 0)
    transunion = credit_score_data.get('transunion', 0)
    total_score = credit_score_data.get('credit_score', 0)
    has_data = credit_score_data.get('has_credit_data', False)
    
    if not has_data:
        return f"Contact {contact_id} does not have credit score validation data.\nNo credit score information has been recorded for this contact."
    
    # If there's analysis data, format it with organized structure
    analysis = credit_score.get('analysis')
    if analysis:
        result = analysis.get('result', 'unknown')
        reason = analysis.get('reason', 'No reason provided')
        credit_score_status = analysis.get('credit_score_status', 'unknown')
        
        # Build organized response
        response_parts = []
        
        # Header with status icon
        if result == 'pass':
            response_parts.append(f"Contact {contact_id} has **acceptable credit score**")
        elif result == 'no_data':
            response_parts.append(f"Contact {contact_id} has **missing credit score data**")
            response_parts.append("⚠️ **Action Required:** Credit score information must be collected and entered into the system.")
        else:
            response_parts.append(f"Contact {contact_id} has **credit score below minimum**")
        
        # Credit score information section
        response_parts.append("")
        response_parts.append("**Credit Score Information:**")
        if has_data and total_score > 0:
            response_parts.append(f"• Equifax: **{equifax}**")
            response_parts.append(f"• Experian: **{experian}**")
            response_parts.append(f"• TransUnion: **{transunion}**")
            response_parts.append(f"• **Total Score: {total_score}**")
        else:
            response_parts.append("• Equifax: **Not Available**")
            response_parts.append("• Experian: **Not Available**")
            response_parts.append("• TransUnion: **Not Available**")
            response_parts.append("• **Total Score: Not Available**")
        
        # Validation results section
        response_parts.append("")
        response_parts.append("**Validation Results:**")
        response_parts.append(f"• Credit Score Status: **{credit_score_status.upper()}**")
        response_parts.append(f"• Overall Result: **{result.upper()}**")
        response_parts.append(f"• Reason: {reason}")
        
        # Summary statement
        if result == 'pass':
            response_parts.append("")
            response_parts.append("**PASS** - Credit score meets minimum requirements.")
        elif result == 'no_data':
            response_parts.append("")
            response_parts.append("**NO DATA** - Credit score information is missing or unavailable.")
            response_parts.append("**Next Steps:** Contact the client to collect credit score information from all three bureaus (Equifax, Experian, TransUnion).")
        else:
            response_parts.append("")
            response_parts.append("**NO PASS** - Credit score is below minimum threshold.")
        
        return "\n".join(response_parts)
    
    return "Unable to format credit score analysis results. Please try again."

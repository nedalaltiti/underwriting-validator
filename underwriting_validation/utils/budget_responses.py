"""
Budget validation response formatters.

This module contains formatting functions specifically for budget validation responses.
"""

from typing import Dict, Any


async def format_budget_response(analysis: Any, budget_data: Any) -> str:
    """Format budget analysis into a user-friendly response."""
    contact_id = budget_data.contact_id
    
    # Format currency values
    income_formatted = f"${analysis.total_net_income:,.2f}"
    expenses_formatted = f"${analysis.total_expenses:,.2f}"
    surplus_formatted = f"${analysis.surplus:,.2f}"
    
    # Build organized response
    response_parts = []
    
    # Header with status icon
    if analysis.result.value == "pass":
        response_parts.append(f"Contact {contact_id} has a **positive budget surplus**\n")
    else:
        response_parts.append(f"Contact {contact_id} has a **negative budget surplus**\n")
    
    # Budget information section
    response_parts.append("**Budget Analysis:**\n")
    response_parts.append(f"• Total Net Income: **{income_formatted}**\n")
    response_parts.append(f"• Total Expenses: **{expenses_formatted}**\n")
    response_parts.append(f"• Surplus/Deficit: **{surplus_formatted}**\n")
    
    # Analysis results section
    response_parts.append("**Validation Result:**\n")
    response_parts.append(f"• Status: **{analysis.result.value.upper()}**\n")
    response_parts.append(f"• Reason: {analysis.reason}\n")
    
    return "\n".join(response_parts)


async def format_budget_analysis_response(budget: Dict[str, Any]) -> str:
    """Format budget analysis results into a user-friendly response."""
    if not budget:
        return "No budget data found for that contact ID."
    
    # If there's a formatted response already provided, use it
    if budget.get('formatted_response'):
        return budget['formatted_response']
    
    # If there's an error, return the error message
    if budget.get('error'):
        return f"Error analyzing budget data: {budget['error']}"
    
    contact_id = budget.get('contact_id', 'Unknown')
    
    # Check if there's budget data available
    budget_data = budget.get('budget_data', {})
    total_net_income = budget_data.get('total_net_income', 0)
    total_expenses = budget_data.get('total_expenses', 0)
    
    has_budget_data = any([total_net_income > 0, total_expenses > 0])
    
    if not has_budget_data:
        return f"Contact {contact_id} does not have budget validation data.\nNo budget information has been recorded for this contact."
    
    # If there's analysis data, format it with organized structure
    analysis = budget.get('analysis')
    if analysis:
        result = analysis.get('result', 'unknown')
        reason = analysis.get('reason', 'No reason provided')
        surplus = analysis.get('surplus', 0)
        
        # Format currency values
        income_formatted = f"${total_net_income:,.2f}"
        expenses_formatted = f"${total_expenses:,.2f}"
        surplus_formatted = f"${surplus:,.2f}"
        
        # Build organized response
        response_parts = []
        
        # Header with status icon
        if result == 'pass':
            response_parts.append(f"Contact {contact_id} has a **positive budget surplus**")
        else:
            response_parts.append(f"Contact {contact_id} has a **negative budget surplus**")
        
        # Budget information section
        response_parts.append("")
        response_parts.append("**Budget Analysis:**")
        response_parts.append(f"• Total Net Income: **{income_formatted}**")
        response_parts.append(f"• Total Expenses: **{expenses_formatted}**")
        response_parts.append(f"• Surplus/Deficit: **{surplus_formatted}**")
        
        # Analysis results section
        response_parts.append("")
        response_parts.append("**Validation Result:**")
        response_parts.append(f"• Status: **{result.upper()}**")
        response_parts.append(f"• Reason: {reason}")
        
        # Summary statement
        if result == 'pass':
            response_parts.append("")
            response_parts.append("**PASS** - This client shows a positive surplus and can be shown to agents.")
        else:
            response_parts.append("")
            response_parts.append("**NO PASS** - This client shows a negative surplus and should not be shown to agents.")
        
        return "\n".join(response_parts)
    
    return "Unable to format budget analysis results. Please try again."

"""
Combined validation response formatters.

This module contains formatting functions for combined validation responses.
"""

from typing import Dict, Any


def format_combined_validation_response(
    contact_id: int,
    hardship_data: Dict[str, Any],
    budget_data: Dict[str, Any],
    address_data: Dict[str, Any],
    hardship_analysis: Any,
    budget_analysis: Any,
    address_analysis: Any,
    combined_result: str
) -> str:
    """Format combined hardship, budget, and address analysis into a comprehensive response."""
    response_parts = []
    
    # Header
    response_parts.append(f"# **Validation Analysis for Contact {contact_id}**\n")
    
    # Overall result
    if combined_result == "pass":
        response_parts.append("## **OVERALL RESULT: PASS**\n")
    elif combined_result == "no_pass":
        response_parts.append("## **OVERALL RESULT: NO PASS**\n")
    elif combined_result == "mixed":
        response_parts.append("## **OVERALL RESULT: MIXED** (Requires Manual Review)\n")
    elif combined_result == "not_eligible":
        response_parts.append("## **OVERALL RESULT: NOT ELIGIBLE**\n")
    else:
        response_parts.append("## **OVERALL RESULT: NO DATA**\n")
    
    # Hardship Analysis Section
    response_parts.append("### **Hardship Validation**\n")
    if hardship_analysis:
        hardship_status = "**PASS**" if hardship_analysis.result.value == "pass" else "**NO PASS**"
        response_parts.append(f"**Status:** {hardship_status}\n")
        response_parts.append(f"**Confidence:** {hardship_analysis.confidence * 100:.1f}%\n")
        response_parts.append(f"**Reason:** {hardship_analysis.reason}\n")
    else:
        response_parts.append("**Status:** No hardship data available\n")
    
    # Budget Analysis Section
    response_parts.append("### **Budget Validation**\n")
    if budget_analysis:
        budget_status = "**PASS**" if budget_analysis.result.value == "pass" else "**NO PASS**"
        response_parts.append(f"**Status:** {budget_status}\n")
        response_parts.append(f"**Reason:** {budget_analysis.reason}\n")
    else:
        response_parts.append("**Status:** No budget data available\n")
    
    # Address Analysis Section
    response_parts.append("### **Address Validation**\n")
    if address_analysis:
        address_status = "**PASS**" if address_analysis.result.value == "pass" else "**NO PASS**"
        response_parts.append(f"**Status:** {address_status}\n")
        response_parts.append(f"**State Check:** {address_analysis.state_check}\n")
        response_parts.append(f"**Reason:** {address_analysis.reason}\n")
    else:
        response_parts.append("**Status:** No address data available\n")
    
    return "\n".join(response_parts)

"""
Draft Response Formats for Underwriting

This module provides response formatting for draft validation analysis.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from .pii_filter import mask_contact_id


async def format_draft_response(analysis, draft_data) -> str:
    """
    Format draft analysis into a user-friendly response.
    
    Args:
        analysis: DraftAnalysis object containing validation results
        draft_data: DraftDataIn object containing input data
        
    Returns:
        Formatted response string
    """
    masked_id = mask_contact_id(draft_data.contact_id)
    
    if analysis.result.value == "pass":
        return (
            f"Draft validation PASSED for contact {masked_id}. "
            f"All {analysis.months_over_250} months meet the $250 minimum payment requirement. "
            f"Average monthly payment: ${analysis.average_monthly_payment:,.2f}. "
            f"Total payments: ${analysis.total_payments:,.2f} across {analysis.payment_count} payments."
        )
    else:
        return (
            f"Draft validation FAILED for contact {masked_id}. "
            f"{analysis.months_under_250} out of {analysis.months_with_data} months do not meet the $250 minimum payment requirement. "
            f"Minimum monthly payment: ${analysis.minimum_monthly_payment:,.2f}. "
            f"Average monthly payment: ${analysis.average_monthly_payment:,.2f}. "
            f"Total payments: ${analysis.total_payments:,.2f} across {analysis.payment_count} payments."
        )


async def format_draft_analysis_response(analysis, draft_data) -> Dict[str, Any]:
    """
    Format draft analysis into a structured response dictionary.
    
    Args:
        analysis: DraftAnalysis object containing validation results
        draft_data: DraftDataIn object containing input data
        
    Returns:
        Dictionary containing formatted draft analysis
    """
    return {
        "contact_id": draft_data.contact_id,
        "result": analysis.result.value,
        "reason": analysis.reason,
        "monthly_payments": [
            {
                "year": payment.year,
                "month": payment.month,
                "total_payment": payment.total_payment,
                "over_250": payment.over_250
            }
            for payment in analysis.monthly_payments
        ],
        "statistics": {
            "total_payments": analysis.total_payments,
            "payment_count": analysis.payment_count,
            "months_with_data": analysis.months_with_data,
            "months_over_250": analysis.months_over_250,
            "months_under_250": analysis.months_under_250,
            "average_monthly_payment": analysis.average_monthly_payment,
            "minimum_monthly_payment": analysis.minimum_monthly_payment
        },
        "message": await format_draft_response(analysis, draft_data)
    }

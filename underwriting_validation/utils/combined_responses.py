"""
Combined validation response formatters.

This module contains formatting functions for combined validation responses.
"""

from typing import Dict, Any, Optional


def format_combined_validation_response(
    contact_id: int,
    hardship_analysis: Any,
    budget_analysis: Any,
    address_analysis: Any,
    contract_analysis: Any,
    combined_result: str,
    contract_data: Optional[Any] = None
) -> str:
    """Format combined hardship, budget, address, and contract analysis into a comprehensive response."""
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
    
    # Contract Analysis Section
    response_parts.append("### **Contract Validation**\n")
    if contract_analysis:
        contract_status = "**PASS**" if contract_analysis.result.value == "pass" else "**NO PASS**"
        response_parts.append(f"**Status:** {contract_status}\n")
        response_parts.append(f"**IP Check:** {contract_analysis.ip_check}\n")
        response_parts.append(f"**Email Check:** {contract_analysis.email_check}\n")
        response_parts.append(f"**Signature Check:** {contract_analysis.signature_check}\n")
        response_parts.append(f"**Bank Check:** {contract_analysis.bank_check}\n")
        response_parts.append(f"**VLP Name Check:** {contract_analysis.name_check}\n")
        response_parts.append(f"**VLP SSN Check:** {contract_analysis.ssn_check}\n")
        response_parts.append(f"**VLP DOB Check:** {contract_analysis.dob_check}\n")
        response_parts.append(f"**VLP Fees Check:** {contract_analysis.fees_check}\n")
        response_parts.append(f"**VLP Plan Check:** {contract_analysis.plan_check}\n")
        response_parts.append(f"**Gateway Signature Check:** {contract_analysis.gateway_signature_check}\n")
        response_parts.append(f"**Payment Count Check:** {contract_analysis.payment_count_check}\n")
        response_parts.append(f"**Payment Amounts Check:** {contract_analysis.payment_amounts_check}\n")
        response_parts.append(f"**Payment Dates Check:** {contract_analysis.payment_dates_check}\n")
        response_parts.append(f"**Reason:** {contract_analysis.reason}\n")
        
        # Display contract details if available
        if hasattr(contract_analysis, 'sender_ip_address') or hasattr(contract_analysis, 'forth_email') or hasattr(contract_analysis, 'client_signature') or hasattr(contract_analysis, 'contract_account_number'):
            response_parts.append("\n**Contract Details:**\n")
            
            # IP Address Data
            if contract_analysis.sender_ip_address or contract_analysis.signer_ip_address:
                response_parts.append(f"• Sender IP: {contract_analysis.sender_ip_address or 'Not available'}")
                response_parts.append(f"• Signer IP: {contract_analysis.signer_ip_address or 'Not available'}")
            
            # Email Data
            if contract_analysis.forth_email or contract_analysis.contract_email:
                response_parts.append(f"• Forth Email: {contract_analysis.forth_email or 'Not available'}")
                response_parts.append(f"• Contract Email: {contract_analysis.contract_email or 'Not available'}")
            
            # Signature Data
            if contract_analysis.client_signature or contract_analysis.coclient_signature:
                response_parts.append(f"• Client Signature: {'Present' if contract_analysis.client_signature else 'Not available'}")
                response_parts.append(f"• Co-Client Signature: {'Present' if contract_analysis.coclient_signature else 'Not available'}")
            
            # Bank Data
            if any([contract_analysis.contract_account_number, contract_analysis.forth_account_number, 
                   contract_analysis.contract_routing_number, contract_analysis.forth_routing_number,
                   contract_analysis.contract_bank_name, contract_analysis.forth_bank_name,
                   contract_analysis.contract_account_type, contract_analysis.forth_account_type,
                   contract_analysis.contract_address, contract_analysis.forth_address]):
                response_parts.append("\n**Bank Details:**")
                if contract_analysis.contract_account_number or contract_analysis.forth_account_number:
                    response_parts.append(f"• Contract Account: {contract_analysis.contract_account_number or 'Not available'}")
                    response_parts.append(f"• Forth Account: {contract_analysis.forth_account_number or 'Not available'}")
                if contract_analysis.contract_routing_number or contract_analysis.forth_routing_number:
                    response_parts.append(f"• Contract Routing: {contract_analysis.contract_routing_number or 'Not available'}")
                    response_parts.append(f"• Forth Routing: {contract_analysis.forth_routing_number or 'Not available'}")
                if contract_analysis.contract_bank_name or contract_analysis.forth_bank_name:
                    response_parts.append(f"• Contract Bank: {contract_analysis.contract_bank_name or 'Not available'}")
                    response_parts.append(f"• Forth Bank: {contract_analysis.forth_bank_name or 'Not available'}")
                if contract_analysis.contract_account_type or contract_analysis.forth_account_type:
                    response_parts.append(f"• Contract Type: {contract_analysis.contract_account_type or 'Not available'}")
                    response_parts.append(f"• Forth Type: {contract_analysis.forth_account_type or 'Not available'}")
                if contract_analysis.contract_address or contract_analysis.forth_address:
                    response_parts.append(f"• Contract Address: {contract_analysis.contract_address or 'Not available'}")
                    response_parts.append(f"• Forth Address: {contract_analysis.forth_address or 'Not available'}")
            
            # VLP Data
            if any([contract_analysis.legal_plan_provider, contract_analysis.contract_name, contract_analysis.forth_name,
                   contract_analysis.contract_ssn, contract_analysis.forth_ssn, contract_analysis.contract_dob, contract_analysis.forth_dob,
                   contract_analysis.legal_setup_fee_snapshot, contract_analysis.legal_monthly_fee_snapshot,
                   contract_analysis.legal_setup_fee_enrollment, contract_analysis.legal_monthly_fee_enrollment,
                   contract_analysis.plan_name]):
                response_parts.append("\n**VLP Details:**")
                if contract_analysis.legal_plan_provider:
                    response_parts.append(f"• Legal Plan Provider: {contract_analysis.legal_plan_provider}")
                if contract_analysis.contract_name or contract_analysis.forth_name:
                    response_parts.append(f"• Contract Name: {contract_analysis.contract_name or 'Not available'}")
                    response_parts.append(f"• Forth Name: {contract_analysis.forth_name or 'Not available'}")
                if contract_analysis.contract_ssn or contract_analysis.forth_ssn:
                    response_parts.append(f"• Contract SSN: {contract_analysis.contract_ssn or 'Not available'}")
                    response_parts.append(f"• Forth SSN: {contract_analysis.forth_ssn or 'Not available'}")
                if contract_analysis.contract_dob or contract_analysis.forth_dob:
                    response_parts.append(f"• Contract DOB: {contract_analysis.contract_dob or 'Not available'}")
                    response_parts.append(f"• Forth DOB: {contract_analysis.forth_dob or 'Not available'}")
                if contract_analysis.legal_setup_fee_snapshot or contract_analysis.legal_monthly_fee_snapshot:
                    response_parts.append(f"• Setup Fee (Snapshot): {contract_analysis.legal_setup_fee_snapshot or 'Not available'}")
                    response_parts.append(f"• Monthly Fee (Snapshot): {contract_analysis.legal_monthly_fee_snapshot or 'Not available'}")
                if contract_analysis.legal_setup_fee_enrollment or contract_analysis.legal_monthly_fee_enrollment:
                    response_parts.append(f"• Setup Fee (Enrollment): {contract_analysis.legal_setup_fee_enrollment or 'Not available'}")
                    response_parts.append(f"• Monthly Fee (Enrollment): {contract_analysis.legal_monthly_fee_enrollment or 'Not available'}")
                if contract_analysis.plan_name:
                    response_parts.append(f"• Plan Name: {contract_analysis.plan_name}")
            
            # Gateway Data
            gateway_signature = contract_analysis.gateway_client_signature if hasattr(contract_analysis, 'gateway_client_signature') else (contract_data.get('gateway_client_signature') if contract_data else None)
            contract_payment_count = contract_analysis.contract_payment_count if hasattr(contract_analysis, 'contract_payment_count') else (contract_data.get('contract_payment_count') if contract_data else None)
            forth_payment_count = contract_analysis.forth_payment_count if hasattr(contract_analysis, 'forth_payment_count') else (contract_data.get('forth_payment_count') if contract_data else None)
            payment_details = contract_analysis.payment_details if hasattr(contract_analysis, 'payment_details') else (contract_data.get('payment_details') if contract_data else None)
            
            if any([gateway_signature, contract_payment_count, forth_payment_count, payment_details]):
                response_parts.append("\n**Gateway Details:**")
                if gateway_signature:
                    response_parts.append(f"• Gateway Signature: {gateway_signature}")
                if contract_payment_count or forth_payment_count:
                    response_parts.append(f"• Contract Payment Count: {contract_payment_count or 'Not available'}")
                    response_parts.append(f"• Forth Payment Count: {forth_payment_count or 'Not available'}")
                if payment_details:
                    response_parts.append(f"• Payment Details: {len(payment_details)} payment(s) found")
                    for i, payment in enumerate(payment_details[:3], 1):  # Show first 3 payments
                        response_parts.append(f"  - Payment {i}: Amount {payment.get('amount_check', 'Unknown')}, Date {payment.get('date_check', 'Unknown')}")
                        if payment.get('contract_amount') or payment.get('forth_amount'):
                            response_parts.append(f"    Contract Amount: {payment.get('contract_amount', 'Not available')}, Forth Amount: {payment.get('forth_amount', 'Not available')}")
                        if payment.get('contract_date') or payment.get('forth_date'):
                            response_parts.append(f"    Contract Date: {payment.get('contract_date', 'Not available')}, Forth Date: {payment.get('forth_date', 'Not available')}")
                    if len(payment_details) > 3:
                        response_parts.append(f"  - ... and {len(payment_details) - 3} more payment(s)")
    else:
        response_parts.append("**Status:** No contract data available\n")
    
    return "\n".join(response_parts)

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
    contract_data: Optional[Any] = None,
    duplication_analysis: Optional[Any] = None,
    draft_analysis: Optional[Any] = None
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
        
        # Group validations by category for better organization
        response_parts.append("**Validation Results:**\n")
        
        # IP & Email Section
        response_parts.append("**Identity & Communication:**")
        response_parts.append(f"  • IP Address Validation: {contract_analysis.ip_address_validation}")
        response_parts.append(f"  • Email Address Validation: {contract_analysis.email_address_validation}\n")
        
        # Signature Section
        response_parts.append("**Signature Validation:**")
        response_parts.append(f"  • Signature Validation: {contract_analysis.signature_validation}\n")
        
        # Bank Section
        response_parts.append("**Bank Account Validation:**")
        response_parts.append(f"  • Bank Account Validation: {contract_analysis.bank_account_validation}\n")
        
        # VLP Section
        response_parts.append("**VLP (Voluntary Legal Plan) Validation:**")
        response_parts.append(f"  • Name Validation: {contract_analysis.vlp_name_validation}")
        response_parts.append(f"  • SSN Validation: {contract_analysis.ssn_consistency_validation}")
        response_parts.append(f"  • DOB Validation: {contract_analysis.dob_consistency_validation}")
        response_parts.append(f"  • Fees Validation: {contract_analysis.vlp_fees_validation}")
        response_parts.append(f"  • Plan Validation: {contract_analysis.vlp_plan_validation}\n")
        
        # Gateway Section
        response_parts.append("**Payment Gateway Validation:**")
        response_parts.append(f"  • Gateway Signature: {contract_analysis.gateway_signature_validation}")
        response_parts.append(f"  • Payment Count: {contract_analysis.payment_count_validation}")
        response_parts.append(f"  • Payment Amounts: {contract_analysis.payment_amounts_validation}")
        response_parts.append(f"  • Payment Dates: {contract_analysis.payment_dates_validation}\n")
        
        # SSN & DOB Section
        response_parts.append("**Identity Consistency:**")
        response_parts.append(f"  • SSN Consistency: {contract_analysis.ssn_consistency_validation}")
        response_parts.append(f"  • DOB Consistency: {contract_analysis.dob_consistency_validation}")
        response_parts.append(f"  • Age Eligibility: {contract_analysis.age_eligibility_validation}\n")
        
        # Debts Section
        response_parts.append("**Debt Validation:**")
        response_parts.append(f"  • Debt Count Validation: {contract_analysis.debt_count_validation}\n")
        
        response_parts.append(f"**Reason:** {contract_analysis.reason}\n")
        
        # Display contract details if available
        if hasattr(contract_analysis, 'sender_ip_address') or hasattr(contract_analysis, 'forth_email') or hasattr(contract_analysis, 'client_signature') or hasattr(contract_analysis, 'contract_account_number'):
            response_parts.append("\n**Contract Details:**\n")
            
            # IP Address Data
            if contract_analysis.sender_ip_address or contract_analysis.signer_ip_address:
                response_parts.append("**IP Address Information:**")
                response_parts.append(f"  • Sender IP: {contract_analysis.sender_ip_address or 'Not available'}")
                response_parts.append(f"  • Signer IP: {contract_analysis.signer_ip_address or 'Not available'}\n")
            
            # Email Data
            if contract_analysis.forth_email or contract_analysis.contract_email:
                response_parts.append("**Email Information:**")
                response_parts.append(f"  • Forth Email: {contract_analysis.forth_email or 'Not available'}")
                response_parts.append(f"  • Contract Email: {contract_analysis.contract_email or 'Not available'}\n")
            
            # Signature Data
            if contract_analysis.client_signature or contract_analysis.coclient_signature:
                response_parts.append("**Signature Information:**")
                response_parts.append(f"  • Client Signature: {'Present' if contract_analysis.client_signature else 'Not available'}")
                response_parts.append(f"  • Co-Client Signature: {'Present' if contract_analysis.coclient_signature else 'Not available'}\n")
            
            # Bank Data
            if any([contract_analysis.contract_account_number, contract_analysis.forth_account_number,
                    contract_analysis.contract_routing_number, contract_analysis.forth_routing_number,
                    contract_analysis.contract_bank_name, contract_analysis.forth_bank_name,
                    contract_analysis.contract_account_type, contract_analysis.forth_account_type,
                    contract_analysis.contract_address, contract_analysis.forth_address]):
                response_parts.append("**Bank Account Information:**")
                if contract_analysis.contract_account_number or contract_analysis.forth_account_number:
                    response_parts.append(f"  • Contract Account: {contract_analysis.contract_account_number or 'Not available'}")
                    response_parts.append(f"  • Forth Account: {contract_analysis.forth_account_number or 'Not available'}")
                if contract_analysis.contract_routing_number or contract_analysis.forth_routing_number:
                    response_parts.append(f"  • Contract Routing: {contract_analysis.contract_routing_number or 'Not available'}")
                    response_parts.append(f"  • Forth Routing: {contract_analysis.forth_routing_number or 'Not available'}")
                if contract_analysis.contract_bank_name or contract_analysis.forth_bank_name:
                    response_parts.append(f"  • Contract Bank: {contract_analysis.contract_bank_name or 'Not available'}")
                    response_parts.append(f"  • Forth Bank: {contract_analysis.forth_bank_name or 'Not available'}")
                if contract_analysis.contract_account_type or contract_analysis.forth_account_type:
                    response_parts.append(f"  • Contract Type: {contract_analysis.contract_account_type or 'Not available'}")
                    response_parts.append(f"  • Forth Type: {contract_analysis.forth_account_type or 'Not available'}")
                if contract_analysis.contract_address or contract_analysis.forth_address:
                    response_parts.append(f"  • Contract Address: {contract_analysis.contract_address or 'Not available'}")
                    response_parts.append(f"  • Forth Address: {contract_analysis.forth_address or 'Not available'}")
                response_parts.append("")
            
            # VLP Data
            if any([contract_analysis.legal_plan_provider, contract_analysis.contract_name, contract_analysis.forth_name,
                    contract_analysis.contract_ssn, contract_analysis.forth_ssn, contract_analysis.contract_dob, contract_analysis.forth_dob,
                    contract_analysis.legal_setup_fee_snapshot, contract_analysis.legal_monthly_fee_snapshot,
                    contract_analysis.legal_setup_fee_enrollment, contract_analysis.legal_monthly_fee_enrollment,
                    contract_analysis.plan_name]):
                response_parts.append("**VLP (Voluntary Legal Plan) Information:**")
                if contract_analysis.legal_plan_provider:
                    response_parts.append(f"  • Legal Plan Provider: {contract_analysis.legal_plan_provider}")
                if contract_analysis.contract_name or contract_analysis.forth_name:
                    response_parts.append(f"  • Contract Name: {contract_analysis.contract_name or 'Not available'}")
                    response_parts.append(f"  • Forth Name: {contract_analysis.forth_name or 'Not available'}")
                if contract_analysis.contract_ssn or contract_analysis.forth_ssn:
                    response_parts.append(f"  • Contract SSN: {contract_analysis.contract_ssn or 'Not available'}")
                    response_parts.append(f"  • Forth SSN: {contract_analysis.forth_ssn or 'Not available'}")
                if contract_analysis.contract_dob or contract_analysis.forth_dob:
                    response_parts.append(f"  • Contract DOB: {contract_analysis.contract_dob or 'Not available'}")
                    response_parts.append(f"  • Forth DOB: {contract_analysis.forth_dob or 'Not available'}")
                if contract_analysis.legal_setup_fee_snapshot or contract_analysis.legal_monthly_fee_snapshot:
                    response_parts.append(f"  • Setup Fee (Snapshot): {contract_analysis.legal_setup_fee_snapshot or 'Not available'}")
                    response_parts.append(f"  • Monthly Fee (Snapshot): {contract_analysis.legal_monthly_fee_snapshot or 'Not available'}")
                if contract_analysis.legal_setup_fee_enrollment or contract_analysis.legal_monthly_fee_enrollment:
                    response_parts.append(f"  • Setup Fee (Enrollment): {contract_analysis.legal_setup_fee_enrollment or 'Not available'}")
                    response_parts.append(f"  • Monthly Fee (Enrollment): {contract_analysis.legal_monthly_fee_enrollment or 'Not available'}")
                if contract_analysis.plan_name:
                    response_parts.append(f"  • Plan Name: {contract_analysis.plan_name}")
                response_parts.append("")
            
            # Gateway Data
            gateway_signature = getattr(contract_analysis, 'gateway_client_signature', None)
            contract_payment_count = getattr(contract_analysis, 'contract_payment_count', None)
            forth_payment_count = getattr(contract_analysis, 'forth_payment_count', None)
            payment_details = getattr(contract_analysis, 'payment_details', None)
            
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
            
            # SSN Data
            payment_gateway_ssn = getattr(contract_analysis, 'payment_gateway_agreement_client_ssn', None)
            legal_plan_ssn = getattr(contract_analysis, 'legal_plan_agreement_client_ssn', None)
            power_of_attorney_ssn = getattr(contract_analysis, 'power_of_attorney_client_ssn', None)
            credit_report_ssn = getattr(contract_analysis, 'credit_report_ssn', None)
            
            if any([payment_gateway_ssn, legal_plan_ssn, power_of_attorney_ssn, credit_report_ssn]):
                response_parts.append("\n**SSN Details:**")
                if payment_gateway_ssn:
                    response_parts.append(f"• Payment Gateway SSN: {payment_gateway_ssn}")
                if legal_plan_ssn:
                    response_parts.append(f"• Legal Plan SSN: {legal_plan_ssn}")
                if power_of_attorney_ssn:
                    response_parts.append(f"• Power of Attorney SSN: {power_of_attorney_ssn}")
                if credit_report_ssn:
                    response_parts.append(f"• Credit Report SSN: {credit_report_ssn}")
            
            # DOB Data
            forth_dob = getattr(contract_analysis, 'forth_dob', None)
            contract_dob = getattr(contract_analysis, 'contract_dob', None)
            
            if forth_dob or contract_dob:
                response_parts.append("\n**DOB Details:**")
                if forth_dob:
                    response_parts.append(f"• Forth DOB: {forth_dob}")
                if contract_dob:
                    response_parts.append(f"• Contract DOB: {contract_dob}")
            
            # Debts Data
            forth_debt_count = getattr(contract_analysis, 'forth_debt_count', None)
            contract_debt_count = getattr(contract_analysis, 'contract_debt_count', None)
            
            if forth_debt_count is not None or contract_debt_count is not None:
                response_parts.append("\n**Debts Details:**")
                if forth_debt_count is not None:
                    response_parts.append(f"• Forth Debt Count: {forth_debt_count}")
                if contract_debt_count is not None:
                    response_parts.append(f"• Contract Debt Count: {contract_debt_count}")
            
            # Add payment details continuation if needed
            if payment_details and len(payment_details) > 3:
                response_parts.append(f"  - ... and {len(payment_details) - 3} more payment(s)")
    else:
        response_parts.append("**Status:** No contract data available\n")
    
    # Duplication Analysis Section
    response_parts.append("### **Duplication Validation**\n")
    if duplication_analysis:
        # Handle both DuplicationAnalysis object and dictionary
        if hasattr(duplication_analysis, 'has_duplicates'):
            # It's a DuplicationAnalysis object
            duplication_status = "**NO PASS**" if duplication_analysis.has_duplicates else "**PASS**"
            response_parts.append(f"**Status:** {duplication_status}\n")
            response_parts.append(f"**SSN Duplicates:** {duplication_analysis.ssn_duplicate_count}\n")
            response_parts.append(f"**Phone Duplicates:** {duplication_analysis.phone_duplicate_count}\n")
            response_parts.append(f"**Reason:** {duplication_analysis.reason}\n")
            
            # Show duplicate details if any
            ssn_duplicates = duplication_analysis.ssn_duplicates
            phone_duplicates = duplication_analysis.phone_duplicates
        else:
            # It's a dictionary (formatted data)
            duplication_status = "**NO PASS**" if duplication_analysis.get('has_duplicates', False) else "**PASS**"
            response_parts.append(f"**Status:** {duplication_status}\n")
            response_parts.append(f"**SSN Duplicates:** {duplication_analysis.get('ssn_duplicate_count', 0)}\n")
            response_parts.append(f"**Phone Duplicates:** {duplication_analysis.get('phone_duplicate_count', 0)}\n")
            response_parts.append(f"**Reason:** {duplication_analysis.get('duplication_reason', 'No reason provided')}\n")
            
            # Show duplicate details if any
            ssn_duplicates = duplication_analysis.get('ssn_duplicates', [])
            phone_duplicates = duplication_analysis.get('phone_duplicates', [])
        
        if ssn_duplicates:
            response_parts.append("**SSN Duplicates Found:**\n")
            for i, duplicate in enumerate(ssn_duplicates[:3], 1):  # Show first 3
                if isinstance(duplicate, dict):
                    response_parts.append(f"  {i}. Contact ID: {duplicate.get('id', 'Unknown')}")
                    response_parts.append(f"     Status: {duplicate.get('contacts_lead_status', 'Unknown')}")
                    response_parts.append(f"     Category: {duplicate.get('contact_categorie', 'Unknown')}\n")
                else:
                    response_parts.append(f"  {i}. Duplicate: {duplicate}\n")
            if len(ssn_duplicates) > 3:
                response_parts.append(f"  ... and {len(ssn_duplicates) - 3} more SSN duplicate(s)\n")
        
        if phone_duplicates:
            response_parts.append("**Phone Duplicates Found:**\n")
            for i, duplicate in enumerate(phone_duplicates[:3], 1):  # Show first 3
                if isinstance(duplicate, dict):
                    response_parts.append(f"  {i}. Contact ID: {duplicate.get('id', 'Unknown')}")
                    response_parts.append(f"     Status: {duplicate.get('contacts_lead_status', 'Unknown')}")
                    response_parts.append(f"     Category: {duplicate.get('contact_categorie', 'Unknown')}\n")
                else:
                    response_parts.append(f"  {i}. Duplicate: {duplicate}\n")
            if len(phone_duplicates) > 3:
                response_parts.append(f"  ... and {len(phone_duplicates) - 3} more phone duplicate(s)\n")
    else:
        response_parts.append("**Status:** No duplication data available\n")
    
    # Draft Analysis Section
    response_parts.append("### **Draft Validation**\n")
    if draft_analysis:
        # Handle both DraftAnalysis object and dictionary
        if hasattr(draft_analysis, 'result'):
            # It's a DraftAnalysis object
            draft_status = "**PASS**" if draft_analysis.result.value == "pass" else "**NO PASS**"
            response_parts.append(f"**Status:** {draft_status}\n")
            response_parts.append(f"**Months with Data:** {draft_analysis.months_with_data}\n")
            response_parts.append(f"**Months Over $250:** {draft_analysis.months_over_250}\n")
            response_parts.append(f"**Months Under $250:** {draft_analysis.months_under_250}\n")
            response_parts.append(f"**Average Monthly Payment:** ${draft_analysis.average_monthly_payment:,.2f}\n")
            response_parts.append(f"**Minimum Monthly Payment:** ${draft_analysis.minimum_monthly_payment:,.2f}\n")
            response_parts.append(f"**Total Payments:** ${draft_analysis.total_payments:,.2f}\n")
            response_parts.append(f"**Payment Count:** {draft_analysis.payment_count}\n")
            response_parts.append(f"**Reason:** {draft_analysis.reason}\n")
            
            # Show monthly payment details if available
            if draft_analysis.monthly_payments:
                response_parts.append("**Monthly Payment Details:**\n")
                for i, payment in enumerate(draft_analysis.monthly_payments[:6], 1):  # Show first 6 months
                    status = "✓" if payment.over_250 else "✗"
                    response_parts.append(f"  {i}. {payment.year}-{payment.month:02d}: ${payment.total_payment:,.2f} {status}\n")
                if len(draft_analysis.monthly_payments) > 6:
                    response_parts.append(f"  ... and {len(draft_analysis.monthly_payments) - 6} more month(s)\n")
        else:
            # It's a dictionary (formatted data)
            draft_status = "**PASS**" if draft_analysis.get('draft_validation_result') == "pass" else "**NO PASS**"
            response_parts.append(f"**Status:** {draft_status}\n")
            response_parts.append(f"**Months with Data:** {draft_analysis.get('months_with_data', 0)}\n")
            response_parts.append(f"**Months Over $250:** {draft_analysis.get('months_over_250', 0)}\n")
            response_parts.append(f"**Months Under $250:** {draft_analysis.get('months_under_250', 0)}\n")
            response_parts.append(f"**Average Monthly Payment:** ${draft_analysis.get('average_monthly_payment', 0):,.2f}\n")
            response_parts.append(f"**Minimum Monthly Payment:** ${draft_analysis.get('minimum_monthly_payment', 0):,.2f}\n")
            response_parts.append(f"**Total Payments:** ${draft_analysis.get('total_payments', 0):,.2f}\n")
            response_parts.append(f"**Payment Count:** {draft_analysis.get('payment_count', 0)}\n")
            response_parts.append(f"**Reason:** {draft_analysis.get('draft_reason', 'No reason provided')}\n")
            
            # Show monthly payment details if available
            monthly_payments = draft_analysis.get('monthly_payments', [])
            if monthly_payments:
                response_parts.append("**Monthly Payment Details:**\n")
                for i, payment in enumerate(monthly_payments[:6], 1):  # Show first 6 months
                    status = "✓" if payment.get('over_250', False) else "✗"
                    response_parts.append(f"  {i}. {payment.get('year', 'Unknown')}-{payment.get('month', 0):02d}: ${payment.get('total_payment', 0):,.2f} {status}\n")
                if len(monthly_payments) > 6:
                    response_parts.append(f"  ... and {len(monthly_payments) - 6} more month(s)\n")
    else:
        response_parts.append("**Status:** No draft data available\n")
    
    return "\n".join(response_parts)

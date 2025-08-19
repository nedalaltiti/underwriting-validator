"""
Contract Validation Response Formats

This module provides formatting functions for contract validation responses.
"""

from typing import Dict, Any, Optional
from underwriting_validation.utils.pii_filter import mask_contact_id


def format_contract_response(analysis, contract_data) -> str:
    """
    Format contract validation analysis into a user-friendly response.
    
    Args:
        analysis: ContractAnalysis object containing validation results
        contract_data: ContractDataIn object containing input data
        
    Returns:
        Formatted string response
    """
    masked_id = mask_contact_id(contract_data.contact_id)
    
    if analysis.result.value == "no_data":
        return f"Contract validation for contact {masked_id}: No contract data available for analysis."
    
    response_parts = [f"Contract validation for contact {masked_id}:"]
    
    # IP Address Check
    if analysis.ip_address_validation == "Missing Value":
        response_parts.append("- IP Address Check: Missing sender or signer IP address data")
    elif analysis.ip_address_validation == "Match":
        response_parts.append("- IP Address Check: PASS - Sender and signer IP addresses differ")
    elif analysis.ip_address_validation == "Mismatch":
        response_parts.append("- IP Address Check: FAIL - Sender and signer IP addresses are the same")
    
    # Email Check
    if analysis.email_address_validation == "Missing Value":
        response_parts.append("- Email Check: Missing Forth or contract email data")
    elif analysis.email_address_validation == "Match":
        response_parts.append("- Email Check: PASS - Forth email matches contract email")
    elif analysis.email_address_validation == "Mismatch":
        response_parts.append("- Email Check: FAIL - Forth email does not match contract email")
    
    # Signature Check
    if analysis.signature_validation == "Missing Value":
        response_parts.append("- Signature Check: Missing signature data")
    elif analysis.signature_validation == "Valid":
        response_parts.append("- Signature Check: PASS - Signatures follow Forth's requirements")
    elif analysis.signature_validation == "Invalid":
        response_parts.append("- Signature Check: FAIL - Signatures contain invalid characters (dots/dashes)")
    
    # Bank Details Check
    if analysis.bank_account_validation == "Missing Value":
        response_parts.append("- Bank Details Check: Missing bank data")
    elif analysis.bank_account_validation == "Match":
        response_parts.append("- Bank Details Check: PASS - Bank details match between contract and Forth")
    elif analysis.bank_account_validation == "Mismatch":
        response_parts.append("- Bank Details Check: FAIL - Bank details do not match between contract and Forth")
    
    # Overall Result
    if analysis.result.value == "pass":
        response_parts.append(f"\nOverall Result: PASS - {analysis.reason}")
    elif analysis.result.value == "no_pass":
        response_parts.append(f"\nOverall Result: FAIL - {analysis.reason}")
    elif analysis.result.value == "mixed":
        response_parts.append(f"\nOverall Result: MIXED - {analysis.reason}")
    
    return "\n".join(response_parts)


def format_contract_analysis_response(contract_data: Dict[str, Any]) -> str:
    """
    Format contract data into a user-friendly response.
    
    Args:
        contract_data: Dictionary containing contract validation data
        
    Returns:
        Formatted string response
    """
    contact_id = contract_data.get('contact_id')
    masked_id = mask_contact_id(contact_id) if contact_id else "Unknown"
    
    response_parts = [f"Contract data for contact {masked_id}:"]
    
    # IP Address Data
    sender_ip = contract_data.get('sender_ip_address')
    signer_ip = contract_data.get('signer_ip_address')
    if sender_ip or signer_ip:
        response_parts.append(f"- Sender IP: {sender_ip or 'Not available'}")
        response_parts.append(f"- Signer IP: {signer_ip or 'Not available'}")
    else:
        response_parts.append("- IP Address Data: Not available")
    
    # Email Data
    forth_email = contract_data.get('forth_email')
    contract_email = contract_data.get('contract_email')
    if forth_email or contract_email:
        response_parts.append(f"- Forth Email: {forth_email or 'Not available'}")
        response_parts.append(f"- Contract Email: {contract_email or 'Not available'}")
    else:
        response_parts.append("- Email Data: Not available")
    
    # Signature Data
    client_signature = contract_data.get('client_signature')
    coclient_signature = contract_data.get('coclient_signature')
    if client_signature or coclient_signature:
        response_parts.append(f"- Client Signature: {'Present' if client_signature else 'Not available'}")
        response_parts.append(f"- Co-Client Signature: {'Present' if coclient_signature else 'Not available'}")
    else:
        response_parts.append("- Signature Data: Not available")
    
    # Bank Data
    contract_account = contract_data.get('contract_account_number')
    forth_account = contract_data.get('forth_account_number')
    contract_routing = contract_data.get('contract_routing_number')
    forth_routing = contract_data.get('forth_routing_number')
    contract_bank = contract_data.get('contract_bank_name')
    forth_bank = contract_data.get('forth_bank_name')
    contract_type = contract_data.get('contract_account_type')
    forth_type = contract_data.get('forth_account_type')
    contract_addr = contract_data.get('contract_address')
    forth_addr = contract_data.get('forth_address')
    
    if any([contract_account, forth_account, contract_routing, forth_routing, contract_bank, forth_bank, contract_type, forth_type, contract_addr, forth_addr]):
        response_parts.append("")
        response_parts.append("Bank Details:")
        if contract_account or forth_account:
            response_parts.append(f"- Contract Account: {contract_account or 'Not available'}")
            response_parts.append(f"- Forth Account: {forth_account or 'Not available'}")
        if contract_routing or forth_routing:
            response_parts.append(f"- Contract Routing: {contract_routing or 'Not available'}")
            response_parts.append(f"- Forth Routing: {forth_routing or 'Not available'}")
        if contract_bank or forth_bank:
            response_parts.append(f"- Contract Bank: {contract_bank or 'Not available'}")
            response_parts.append(f"- Forth Bank: {forth_bank or 'Not available'}")
        if contract_type or forth_type:
            response_parts.append(f"- Contract Type: {contract_type or 'Not available'}")
            response_parts.append(f"- Forth Type: {forth_type or 'Not available'}")
        if contract_addr or forth_addr:
            response_parts.append(f"- Contract Address: {contract_addr or 'Not available'}")
            response_parts.append(f"- Forth Address: {forth_addr or 'Not available'}")
    else:
        response_parts.append("")
        response_parts.append("Bank Data: Not available")
    
    return "\n".join(response_parts)

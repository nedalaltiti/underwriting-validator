"""
Contract Validation Data Models

This module contains all data models used for contract validation.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import date
from pydantic import BaseModel


class ContractDataIn(BaseModel):
    """Input model for contract validation data."""
    contact_id: int
    sender_ip_address: Optional[str] = None
    signer_ip_address: Optional[str] = None
    forth_email: Optional[str] = None
    contract_email: Optional[str] = None
    client_signature: Optional[str] = None
    client_signature_date: Optional[str] = None
    coclient_signature: Optional[str] = None
    coclient_signature_date: Optional[str] = None
    # Bank details
    contract_account_number: Optional[str] = None
    forth_account_number: Optional[str] = None
    contract_routing_number: Optional[str] = None
    forth_routing_number: Optional[str] = None
    contract_bank_name: Optional[str] = None
    forth_bank_name: Optional[str] = None
    contract_account_type: Optional[str] = None
    forth_account_type: Optional[str] = None
    contract_address: Optional[str] = None
    forth_address: Optional[str] = None
    # VLP details
    legal_plan_provider: Optional[str] = None
    vlp_client_signature: Optional[str] = None
    vlp_signature_date: Optional[str] = None
    contract_name: Optional[str] = None
    forth_name: Optional[str] = None
    contract_ssn: Optional[str] = None
    forth_ssn: Optional[str] = None
    contract_dob: Optional[date] = None
    forth_dob: Optional[date] = None
    legal_setup_fee_snapshot: Optional[str] = None
    legal_monthly_fee_snapshot: Optional[str] = None
    legal_setup_fee_enrollment: Optional[str] = None
    legal_monthly_fee_enrollment: Optional[str] = None
    payment_date: Optional[str] = None
    plan_name: Optional[str] = None
    gateway_client_signature: Optional[str] = None
    contract_payment_count: Optional[int] = None
    forth_payment_count: Optional[int] = None
    count_check: Optional[str] = None
    payment_details: Optional[List[Dict[str, Any]]] = None
    # SSN validation fields
    payment_gateway_agreement_client_ssn: Optional[str] = None
    legal_plan_agreement_client_ssn: Optional[str] = None
    power_of_attorney_client_ssn: Optional[str] = None
    credit_report_ssn: Optional[str] = None
    ssn_check: Optional[str] = None
    # DOB validation fields
    forth_dob: Optional[date] = None
    contract_dob: Optional[date] = None
    dob_check: Optional[str] = None
    age_plus_18_check: Optional[str] = None
    # Debts validation fields
    forth_debt_count: Optional[int] = None
    contract_debt_count: Optional[int] = None
    debt_count_check: Optional[str] = None


class ContractValidity(Enum):
    """Enum for contract validation results."""
    PASS = "pass"
    NO_PASS = "no_pass"
    MIXED = "mixed"
    NO_DATA = "no_data"


@dataclass
class ContractAnalysis:
    """Result of contract validation analysis with embedded validation results."""
    result: ContractValidity  # "pass", "no_pass", "mixed", or "no_data"
    reason: str
    
    # IP validation data and result
    sender_ip_address: Optional[str] = None
    signer_ip_address: Optional[str] = None
    ip_address_validation: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    
    # Email validation data and result
    forth_email: Optional[str] = None
    contract_email: Optional[str] = None
    email_address_validation: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    
    # Signature validation data and result
    client_signature: Optional[str] = None
    coclient_signature: Optional[str] = None
    signature_validation: str = "Missing Value"  # "Valid", "Invalid", or "Missing Value"
    
    # Bank validation data and result
    contract_account_number: Optional[str] = None
    forth_account_number: Optional[str] = None
    contract_routing_number: Optional[str] = None
    forth_routing_number: Optional[str] = None
    contract_bank_name: Optional[str] = None
    forth_bank_name: Optional[str] = None
    contract_account_type: Optional[str] = None
    forth_account_type: Optional[str] = None
    contract_address: Optional[str] = None
    forth_address: Optional[str] = None
    bank_account_validation: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    
    # VLP validation data and results
    legal_plan_provider: Optional[str] = None
    vlp_client_signature: Optional[str] = None
    vlp_signature_date: Optional[str] = None
    contract_name: Optional[str] = None
    forth_name: Optional[str] = None
    contract_ssn: Optional[str] = None
    forth_ssn: Optional[str] = None
    legal_setup_fee_snapshot: Optional[str] = None
    legal_monthly_fee_snapshot: Optional[str] = None
    legal_setup_fee_enrollment: Optional[str] = None
    legal_monthly_fee_enrollment: Optional[str] = None
    payment_date: Optional[str] = None
    plan_name: Optional[str] = None
    vlp_name_validation: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    vlp_fees_validation: str = "Missing Value"  # "Valid", "Invalid", or "Missing Value"
    vlp_plan_validation: str = "Missing Value"  # "Valid", "Invalid", or "Missing Value"
    
    # Gateway validation data and results
    gateway_client_signature: Optional[str] = None
    contract_payment_count: Optional[int] = None
    forth_payment_count: Optional[int] = None
    payment_details: Optional[List[Dict[str, Any]]] = None
    gateway_signature_validation: str = "Missing Value"  # "Valid", "Invalid", or "Missing Value"
    payment_count_validation: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    payment_amounts_validation: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    payment_dates_validation: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    
    # SSN validation data and result
    payment_gateway_agreement_client_ssn: Optional[str] = None
    legal_plan_agreement_client_ssn: Optional[str] = None
    power_of_attorney_client_ssn: Optional[str] = None
    credit_report_ssn: Optional[str] = None
    ssn_consistency_validation: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    
    # DOB validation data and results
    forth_dob: Optional[date] = None
    contract_dob: Optional[date] = None
    dob_consistency_validation: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    age_eligibility_validation: str = "Missing Value"  # "Yes", "No", or "Unknown Age"
    
    # Debts validation data and result
    forth_debt_count: Optional[int] = None
    contract_debt_count: Optional[int] = None
    debt_count_validation: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"

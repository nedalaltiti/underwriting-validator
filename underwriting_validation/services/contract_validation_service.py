"""
Contract Validation Service for Underwriting

Validates contract-related data including IP addresses, email matching, and signature requirements.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


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
    contract_dob: Optional[str] = None
    forth_dob: Optional[str] = None
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
    payment_details: Optional[list] = None


class ContractValidity(Enum):
    """Enum for contract validation results."""
    PASS = "pass"
    NO_PASS = "no_pass"
    MIXED = "mixed"
    NO_DATA = "no_data"


@dataclass
class ContractAnalysis:
    """Result of contract validation analysis."""
    result: ContractValidity  # "pass", "no_pass", "mixed", or "no_data"
    reason: str
    ip_check: str  # "Match", "Mismatch", or "Missing Value"
    email_check: str  # "Match", "Mismatch", or "Missing Value"
    signature_check: str  # "Valid", "Invalid", or "Missing Value"
    bank_check: str  # "Match", "Mismatch", or "Missing Value"
    sender_ip_address: Optional[str] = None
    signer_ip_address: Optional[str] = None
    forth_email: Optional[str] = None
    contract_email: Optional[str] = None
    client_signature: Optional[str] = None
    coclient_signature: Optional[str] = None
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
    contract_dob: Optional[str] = None
    forth_dob: Optional[str] = None
    legal_setup_fee_snapshot: Optional[str] = None
    legal_monthly_fee_snapshot: Optional[str] = None
    legal_setup_fee_enrollment: Optional[str] = None
    legal_monthly_fee_enrollment: Optional[str] = None
    payment_date: Optional[str] = None
    plan_name: Optional[str] = None
    # Gateway details
    gateway_client_signature: Optional[str] = None
    contract_payment_count: Optional[int] = None
    forth_payment_count: Optional[int] = None
    payment_details: Optional[list] = None
    # VLP validation results
    name_check: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    ssn_check: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    dob_check: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    fees_check: str = "Missing Value"  # "Valid", "Invalid", or "Missing Value"
    plan_check: str = "Missing Value"  # "Valid", "Invalid", or "Missing Value"
    # Gateway validation results
    gateway_signature_check: str = "Missing Value"  # "Valid", "Invalid", or "Missing Value"
    payment_count_check: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    payment_amounts_check: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"
    payment_dates_check: str = "Missing Value"  # "Match", "Mismatch", or "Missing Value"


class ContractValidationService:
    """Service for validating contract-related data."""
    
    def __init__(self):
        """Initialize the contract validation service."""
        logger.info("ContractValidationService initialized")
    
    def _validate_ip_addresses(self, sender_ip: Optional[str], signer_ip: Optional[str]) -> str:
        """Validate that sender and signer IP addresses differ."""
        if not sender_ip or not signer_ip:
            return "Missing Value"
        
        # Normalize IP addresses by trimming whitespace
        sender_ip = sender_ip.strip()
        signer_ip = signer_ip.strip()
        
        if sender_ip == signer_ip:
            return "Mismatch"
        else:
            return "Match"
    
    def _validate_email_match(self, forth_email: Optional[str], contract_email: Optional[str]) -> str:
        """Validate that Forth email matches contract email."""
        if not forth_email or forth_email == '' or not contract_email or contract_email == '':
            return "Missing Value"
        
        # Normalize emails by trimming whitespace and converting to lowercase
        forth_email = forth_email.strip().lower()
        contract_email = contract_email.strip().lower()
        
        if forth_email == contract_email:
            return "Match"
        else:
            return "Mismatch"
    
    def _validate_signatures(self, client_signature: Optional[str], coclient_signature: Optional[str]) -> str:
        """Validate signatures follow Forth's requirements."""
        if not client_signature and not coclient_signature:
            return "Missing Value"
        
        # Check for invalid characters (dots/dashes) in signatures
        invalid_chars = ['.', '-']
        
        if client_signature:
            client_sig = client_signature.strip()
            if any(char in client_sig for char in invalid_chars):
                return "Invalid"
        
        if coclient_signature:
            coclient_sig = coclient_signature.strip()
            if any(char in coclient_sig for char in invalid_chars):
                return "Invalid"
        
        return "Valid"
    
    def _validate_bank_details(self, contract_data: dict, forth_data: dict) -> str:
        """Validate that bank details match between contract and Forth."""
        # Check if we have any bank data at all
        has_contract_bank_data = any([
            contract_data.get('account_number'),
            contract_data.get('routing_number'),
            contract_data.get('bank_name'),
            contract_data.get('account_type'),
            contract_data.get('address')
        ])
        
        has_forth_bank_data = any([
            forth_data.get('account_num'),
            forth_data.get('routing_num'),
            forth_data.get('bank_name'),
            forth_data.get('account_type'),
            forth_data.get('bank_address')
        ])
        
        if not has_contract_bank_data and not has_forth_bank_data:
            return "Missing Value"
        
        # Check each field for matching
        checks = []
        
        # Account number check
        contract_account = contract_data.get('account_number')
        forth_account = forth_data.get('account_num')
        if contract_account and forth_account:
            checks.append(contract_account.strip() == forth_account.strip())
        elif contract_account or forth_account:
            checks.append(False)  # One has data, other doesn't
        
        # Routing number check
        contract_routing = contract_data.get('routing_number')
        forth_routing = forth_data.get('routing_num')
        if contract_routing and forth_routing:
            checks.append(contract_routing.strip() == forth_routing.strip())
        elif contract_routing or forth_routing:
            checks.append(False)
        
        # Bank name check
        contract_bank = contract_data.get('bank_name')
        forth_bank = forth_data.get('bank_name')
        if contract_bank and forth_bank:
            checks.append(contract_bank.strip().lower() == forth_bank.strip().lower())
        elif contract_bank or forth_bank:
            checks.append(False)
        
        # Account type check
        contract_type = contract_data.get('account_type')
        forth_type = forth_data.get('account_type')
        if contract_type and forth_type:
            # Normalize account types
            contract_normalized = self._normalize_account_type(contract_type.strip())
            forth_normalized = self._normalize_account_type(forth_type.strip())
            checks.append(contract_normalized == forth_normalized)
        elif contract_type or forth_type:
            checks.append(False)
        
        # Address check
        contract_addr = contract_data.get('address')
        forth_addr = forth_data.get('bank_address')
        if contract_addr and forth_addr:
            checks.append(contract_addr.strip().lower() == forth_addr.strip().lower())
        elif contract_addr or forth_addr:
            checks.append(False)
        
        # If we have any checks, determine overall result
        if checks:
            if all(checks):
                return "Match"
            else:
                return "Mismatch"
        
        return "Missing Value"
    
    def _normalize_account_type(self, account_type: Optional[str]) -> str:
        """Normalize account type for comparison."""
        if not account_type:
            return ''
        account_type = account_type.strip().lower()
        if account_type in ['1', 'checking', 'checking account']:
            return 'checking'
        elif account_type in ['2', 'savings', 'savings account']:
            return 'savings'
        else:
            return account_type
    
    def _validate_vlp_name_match(self, contract_name: Optional[str], forth_name: Optional[str]) -> str:
        """Validate that contract name matches Forth name."""
        if not contract_name or contract_name == '' or not forth_name or forth_name == '':
            return "Missing Value"
        
        # Normalize names by trimming whitespace
        contract_name = contract_name.strip()
        forth_name = forth_name.strip()
        
        if contract_name == forth_name:
            return "Match"
        else:
            return "Mismatch"
    
    def _validate_vlp_ssn_match(self, contract_ssn: Optional[str], forth_ssn: Optional[str]) -> str:
        """Validate that contract SSN matches Forth SSN."""
        if not contract_ssn or contract_ssn == '' or not forth_ssn or forth_ssn == '':
            return "Missing Value"
        
        # Normalize SSNs by trimming whitespace
        contract_ssn = contract_ssn.strip()
        forth_ssn = forth_ssn.strip()
        
        if contract_ssn == forth_ssn:
            return "Match"
        else:
            return "Mismatch"
    
    def _validate_vlp_dob_match(self, contract_dob: Optional[str], forth_dob: Optional[str]) -> str:
        """Validate that contract DOB matches Forth DOB."""
        if not contract_dob or not forth_dob:
            return "Missing Value"
        
        # Convert dates to strings for comparison
        contract_dob_str = str(contract_dob) if contract_dob else ""
        forth_dob_str = str(forth_dob) if forth_dob else ""
        
        if contract_dob_str == forth_dob_str:
            return "Match"
        else:
            return "Mismatch"
    
    def _validate_vlp_fees(self, setup_fee_snapshot: Optional[str], monthly_fee_snapshot: Optional[str],
                          setup_fee_enrollment: Optional[str], monthly_fee_enrollment: Optional[str]) -> str:
        """Validate that VLP fees exist in both client snapshot and enrollment tab."""
        has_snapshot_fees = setup_fee_snapshot or monthly_fee_snapshot
        has_enrollment_fees = setup_fee_enrollment or monthly_fee_enrollment
        
        if not has_snapshot_fees and not has_enrollment_fees:
            return "Missing Value"
        
        if has_snapshot_fees and has_enrollment_fees:
            return "Valid"
        else:
            return "Invalid"  # Only one source has fees
    
    def _validate_vlp_plan_name(self, plan_name: Optional[str]) -> str:
        """Validate that enrollment plan name contains 'w/VLP'."""
        if not plan_name or plan_name == '':
            return "Missing Value"
        
        plan_name_lower = plan_name.strip().lower()
        if 'w/vlp' in plan_name_lower:
            return "Valid"
        else:
            return "Invalid"
    
    def _validate_gateway_signature(self, gateway_signature: Optional[str]) -> str:
        """Validate that gateway signature exists."""
        if not gateway_signature or gateway_signature == '':
            return "Missing Value"
        
        # Check for invalid characters (dots/dashes) in signature
        invalid_chars = ['.', '-']
        signature = gateway_signature.strip()
        if any(char in signature for char in invalid_chars):
            return "Invalid"
        
        return "Valid"
    
    def _validate_payment_count(self, contract_count: Optional[int], forth_count: Optional[int]) -> str:
        """Validate that payment counts match between contract and Forth."""
        if contract_count is None or forth_count is None:
            return "Missing Value"
        
        if contract_count == forth_count:
            return "Match"
        else:
            return "Mismatch"
    
    def _validate_payment_amounts_and_dates(self, payment_details: Optional[list]) -> tuple[str, str]:
        """Validate payment amounts and dates from payment details."""
        if not payment_details or len(payment_details) == 0:
            return "Missing Value", "Missing Value"
        
        # Check if all payments have matching amounts and dates
        all_amounts_match = True
        all_dates_match = True
        
        for payment in payment_details:
            if payment.get('amount_check') == 'Mismatch':
                all_amounts_match = False
            if payment.get('date_check') == 'Mismatch':
                all_dates_match = False
        
        amounts_check = "Match" if all_amounts_match else "Mismatch"
        dates_check = "Match" if all_dates_match else "Mismatch"
        
        return amounts_check, dates_check
    
    async def analyze_contract_validity(
        self, 
        contract_data: ContractDataIn
    ) -> Result[ContractAnalysis]:
        """
        Analyze contract data and determine if all validations pass.
        
        Args:
            contract_data: ContractDataIn model containing contract information
            
        Returns:
            Result containing ContractAnalysis
        """
        try:
            contact_id = contract_data.contact_id
            sender_ip = contract_data.sender_ip_address
            signer_ip = contract_data.signer_ip_address
            forth_email = contract_data.forth_email
            contract_email = contract_data.contract_email
            client_signature = contract_data.client_signature
            coclient_signature = contract_data.coclient_signature
            
            # Check if we have any data at all
            has_ip_data = sender_ip or signer_ip
            has_email_data = forth_email or contract_email
            has_signature_data = client_signature or coclient_signature
            has_bank_data = any([
                contract_data.contract_account_number,
                contract_data.forth_account_number,
                contract_data.contract_routing_number,
                contract_data.forth_routing_number,
                contract_data.contract_bank_name,
                contract_data.forth_bank_name,
                contract_data.contract_account_type,
                contract_data.forth_account_type,
                contract_data.contract_address,
                contract_data.forth_address
            ])
            has_vlp_data = any([
                contract_data.legal_plan_provider,
                contract_data.contract_name,
                contract_data.forth_name,
                contract_data.contract_ssn,
                contract_data.forth_ssn,
                contract_data.contract_dob,
                contract_data.forth_dob,
                contract_data.legal_setup_fee_snapshot,
                contract_data.legal_monthly_fee_snapshot,
                contract_data.legal_setup_fee_enrollment,
                contract_data.legal_monthly_fee_enrollment,
                contract_data.plan_name
            ])
            has_gateway_data = any([
                contract_data.gateway_client_signature,
                contract_data.contract_payment_count,
                contract_data.forth_payment_count,
                contract_data.payment_details
            ])
            
            if not has_ip_data and not has_email_data and not has_signature_data and not has_bank_data and not has_vlp_data and not has_gateway_data:
                return Success(ContractAnalysis(
                    result=ContractValidity.NO_DATA,
                    reason="No contract data available for analysis",
                    ip_check="Missing Value",
                    email_check="Missing Value",
                    signature_check="Missing Value",
                    bank_check="Missing Value",
                    sender_ip_address=sender_ip,
                    signer_ip_address=signer_ip,
                    forth_email=forth_email,
                    contract_email=contract_email,
                    client_signature=client_signature,
                    coclient_signature=coclient_signature,
                    contract_account_number=contract_data.contract_account_number,
                    forth_account_number=contract_data.forth_account_number,
                    contract_routing_number=contract_data.contract_routing_number,
                    forth_routing_number=contract_data.forth_routing_number,
                    contract_bank_name=contract_data.contract_bank_name,
                    forth_bank_name=contract_data.forth_bank_name,
                    contract_account_type=contract_data.contract_account_type,
                    forth_account_type=contract_data.forth_account_type,
                    contract_address=contract_data.contract_address,
                    forth_address=contract_data.forth_address
                ))
            
            # Perform individual validations
            ip_check = self._validate_ip_addresses(sender_ip, signer_ip)
            email_check = self._validate_email_match(forth_email, contract_email)
            signature_check = self._validate_signatures(client_signature, coclient_signature)
            
            # Bank details validation
            contract_bank_data = {
                'account_number': contract_data.contract_account_number,
                'routing_number': contract_data.contract_routing_number,
                'bank_name': contract_data.contract_bank_name,
                'account_type': contract_data.contract_account_type,
                'address': contract_data.contract_address
            }
            forth_bank_data = {
                'account_num': contract_data.forth_account_number,
                'routing_num': contract_data.forth_routing_number,
                'bank_name': contract_data.forth_bank_name,
                'account_type': contract_data.forth_account_type,
                'bank_address': contract_data.forth_address
            }
            bank_check = self._validate_bank_details(contract_bank_data, forth_bank_data)
            
            # VLP validation
            name_check = self._validate_vlp_name_match(contract_data.contract_name, contract_data.forth_name)
            ssn_check = self._validate_vlp_ssn_match(contract_data.contract_ssn, contract_data.forth_ssn)
            dob_check = self._validate_vlp_dob_match(contract_data.contract_dob, contract_data.forth_dob)
            fees_check = self._validate_vlp_fees(
                contract_data.legal_setup_fee_snapshot,
                contract_data.legal_monthly_fee_snapshot,
                contract_data.legal_setup_fee_enrollment,
                contract_data.legal_monthly_fee_enrollment
            )
            plan_check = self._validate_vlp_plan_name(contract_data.plan_name)
            
            # Gateway validation
            gateway_signature_check = self._validate_gateway_signature(contract_data.gateway_client_signature)
            payment_count_check = self._validate_payment_count(contract_data.contract_payment_count, contract_data.forth_payment_count)
            payment_amounts_check, payment_dates_check = self._validate_payment_amounts_and_dates(contract_data.payment_details)
            
            # Determine overall result
            checks = [ip_check, email_check, signature_check, bank_check, name_check, ssn_check, dob_check, fees_check, plan_check, 
                     gateway_signature_check, payment_count_check, payment_amounts_check, payment_dates_check]
            valid_checks = [check for check in checks if check in ["Match", "Valid"]]
            missing_checks = [check for check in checks if check == "Missing Value"]
            invalid_checks = [check for check in checks if check in ["Mismatch", "Invalid"]]
            
            if len(valid_checks) == len(checks):
                result = ContractValidity.PASS
                reason = "All contract validations passed"
            elif len(invalid_checks) > 0:
                result = ContractValidity.NO_PASS
                reason = f"Contract validation failed: {', '.join(invalid_checks)}"
            elif len(missing_checks) == len(checks):
                result = ContractValidity.NO_DATA
                reason = "No contract data available for validation"
            else:
                result = ContractValidity.MIXED
                reason = f"Mixed contract validation results: {', '.join(checks)}"
            
            analysis = ContractAnalysis(
                result=result,
                reason=reason,
                ip_check=ip_check,
                email_check=email_check,
                signature_check=signature_check,
                bank_check=bank_check,
                sender_ip_address=sender_ip,
                signer_ip_address=signer_ip,
                forth_email=forth_email,
                contract_email=contract_email,
                client_signature=client_signature,
                coclient_signature=coclient_signature,
                contract_account_number=contract_data.contract_account_number,
                forth_account_number=contract_data.forth_account_number,
                contract_routing_number=contract_data.contract_routing_number,
                forth_routing_number=contract_data.forth_routing_number,
                contract_bank_name=contract_data.contract_bank_name,
                forth_bank_name=contract_data.forth_bank_name,
                contract_account_type=contract_data.contract_account_type,
                forth_account_type=contract_data.forth_account_type,
                contract_address=contract_data.contract_address,
                forth_address=contract_data.forth_address,
                # VLP details
                legal_plan_provider=contract_data.legal_plan_provider,
                vlp_client_signature=contract_data.vlp_client_signature,
                vlp_signature_date=contract_data.vlp_signature_date,
                contract_name=contract_data.contract_name,
                forth_name=contract_data.forth_name,
                contract_ssn=contract_data.contract_ssn,
                forth_ssn=contract_data.forth_ssn,
                contract_dob=contract_data.contract_dob,
                forth_dob=contract_data.forth_dob,
                legal_setup_fee_snapshot=contract_data.legal_setup_fee_snapshot,
                legal_monthly_fee_snapshot=contract_data.legal_monthly_fee_snapshot,
                legal_setup_fee_enrollment=contract_data.legal_setup_fee_enrollment,
                legal_monthly_fee_enrollment=contract_data.legal_monthly_fee_enrollment,
                payment_date=contract_data.payment_date,
                plan_name=contract_data.plan_name,
                # Gateway details
                gateway_client_signature=contract_data.gateway_client_signature,
                contract_payment_count=contract_data.contract_payment_count,
                forth_payment_count=contract_data.forth_payment_count,
                payment_details=contract_data.payment_details,
                # VLP validation results
                name_check=name_check,
                ssn_check=ssn_check,
                dob_check=dob_check,
                fees_check=fees_check,
                plan_check=plan_check,
                # Gateway validation results
                gateway_signature_check=gateway_signature_check,
                payment_count_check=payment_count_check,
                payment_amounts_check=payment_amounts_check,
                payment_dates_check=payment_dates_check
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Contract analysis completed for contact {masked_id}: {analysis.result.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing contract validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    def format_contract_response(self, analysis: ContractAnalysis, contract_data: ContractDataIn) -> str:
        """Format the contract analysis into a user-friendly response."""
        from underwriting_validation.utils.validation_responses import format_contract_response
        return format_contract_response(analysis, contract_data)

"""
Contract Bank Validation Service for Underwriting

Validates bank-related data for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)


class BankValidationDataIn(BaseModel):
    """Input model for bank validation data."""
    contact_id: int
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


class BankValidationResult(Enum):
    """Enum for bank validation results."""
    MATCH = "Match"
    MISMATCH = "Mismatch"
    MISSING_VALUE = "Missing Value"


@dataclass
class BankValidationAnalysis:
    """Result of bank validation analysis."""
    bank_check: BankValidationResult
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


class ContractBankValidationService:
    """Service for validating bank-related data."""
    
    def __init__(self):
        """Initialize the bank validation service."""
        logger.info("ContractBankValidationService initialized")
    
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
    
    def validate_bank_details(self, contract_data: Dict[str, Any], forth_data: Dict[str, Any]) -> BankValidationResult:
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
            return BankValidationResult.MISSING_VALUE
        
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
                return BankValidationResult.MATCH
            else:
                return BankValidationResult.MISMATCH
        
        return BankValidationResult.MISSING_VALUE
    
    async def analyze_bank_validity(
        self, 
        bank_data: BankValidationDataIn
    ) -> Result[BankValidationAnalysis]:
        """
        Analyze bank data and determine if validation passes.
        
        Args:
            bank_data: BankValidationDataIn model containing bank information
            
        Returns:
            Result containing BankValidationAnalysis
        """
        try:
            contact_id = bank_data.contact_id
            
            # Prepare contract and forth data dictionaries
            contract_bank_data = {
                'account_number': bank_data.contract_account_number,
                'routing_number': bank_data.contract_routing_number,
                'bank_name': bank_data.contract_bank_name,
                'account_type': bank_data.contract_account_type,
                'address': bank_data.contract_address
            }
            forth_bank_data = {
                'account_num': bank_data.forth_account_number,
                'routing_num': bank_data.forth_routing_number,
                'bank_name': bank_data.forth_bank_name,
                'account_type': bank_data.forth_account_type,
                'bank_address': bank_data.forth_address
            }
            
            # Perform bank validation
            bank_check = self.validate_bank_details(contract_bank_data, forth_bank_data)
            
            analysis = BankValidationAnalysis(
                bank_check=bank_check,
                contract_account_number=bank_data.contract_account_number,
                forth_account_number=bank_data.forth_account_number,
                contract_routing_number=bank_data.contract_routing_number,
                forth_routing_number=bank_data.forth_routing_number,
                contract_bank_name=bank_data.contract_bank_name,
                forth_bank_name=bank_data.forth_bank_name,
                contract_account_type=bank_data.contract_account_type,
                forth_account_type=bank_data.forth_account_type,
                contract_address=bank_data.contract_address,
                forth_address=bank_data.forth_address
            )
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Bank analysis completed for contact {masked_id}: {analysis.bank_check.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing bank validity: {e}")
            return Error(f"Analysis failed: {str(e)}")
    
    async def format_bank_response(self, analysis: BankValidationAnalysis) -> str:
        """Format the bank analysis into a user-friendly response."""
        if analysis.bank_check == BankValidationResult.MATCH:
            return f"✅ Bank validation passed: Contract and Forth bank details match"
        elif analysis.bank_check == BankValidationResult.MISMATCH:
            return f"❌ Bank validation failed: Contract and Forth bank details do not match"
        else:
            return f"⚠️ Bank validation incomplete: Missing bank data"

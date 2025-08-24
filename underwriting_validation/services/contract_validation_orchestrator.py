"""
Contract Validation Orchestrator

This module orchestrates the execution of specialized contract validation services.
"""

import logging
from typing import Dict, Any
from underwriting_validation.services.contract_models import ContractDataIn, ContractAnalysis, ContractValidity
from underwriting_validation.services.contract_data_analyzer import ContractDataAnalyzer
from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.pii_filter import mask_contact_id

# Import specialized validation services
from underwriting_validation.services.contract_ip_validation_service import ContractIPValidationService, IPValidationDataIn
from underwriting_validation.services.contract_email_validation_service import ContractEmailValidationService, EmailValidationDataIn
from underwriting_validation.services.contract_signature_validation_service import ContractSignatureValidationService, SignatureValidationDataIn
from underwriting_validation.services.contract_bank_validation_service import ContractBankValidationService, BankValidationDataIn
from underwriting_validation.services.contract_vlp_validation_service import ContractVLPValidationService, VLPValidationDataIn
from underwriting_validation.services.contract_gateway_validation_service import ContractGatewayValidationService, GatewayValidationDataIn
from underwriting_validation.services.contract_ssn_validation_service import ContractSSNValidationService, SSNValidationDataIn
from underwriting_validation.services.contract_dob_validation_service import ContractDOBValidationService, DOBValidationDataIn
from underwriting_validation.services.contract_debts_validation_service import ContractDebtsValidationService, DebtsValidationDataIn

logger = logging.getLogger(__name__)


class ContractValidationOrchestrator:
    """Orchestrates the execution of specialized contract validation services."""
    
    def __init__(self):
        """Initialize the orchestrator with specialized validation services."""
        # Initialize specialized validation services
        self.ip_service = ContractIPValidationService()
        self.email_service = ContractEmailValidationService()
        self.signature_service = ContractSignatureValidationService()
        self.bank_service = ContractBankValidationService()
        self.vlp_service = ContractVLPValidationService()
        self.gateway_service = ContractGatewayValidationService()
        self.ssn_service = ContractSSNValidationService()
        self.dob_service = ContractDOBValidationService()
        self.debts_service = ContractDebtsValidationService()
        
        logger.info("ContractValidationOrchestrator initialized with specialized services")
    
    async def execute_validations(self, contract_data: ContractDataIn) -> Result[ContractAnalysis]:
        """
        Execute all applicable contract validations.
        
        Args:
            contract_data: Contract data to validate
            
        Returns:
            Result containing ContractAnalysis
        """
        try:
            contact_id = contract_data.contact_id
            
            # Check if we have any data at all
            if not ContractDataAnalyzer.has_any_data(contract_data):
                return Success(self._create_no_data_analysis(contract_data))
            
            # Get data availability
            data_availability = ContractDataAnalyzer.has_data_available(contract_data)
            
            # Initialize validation results
            validation_results = self._initialize_validation_results()
            
            # Execute IP validation
            if data_availability["ip_data"]:
                ip_result = await self._execute_ip_validation(contract_data)
                if not ip_result.is_error():
                    validation_results["ip_check"] = ip_result.value.ip_check.value
            
            # Execute email validation
            if data_availability["email_data"]:
                email_result = await self._execute_email_validation(contract_data)
                if not email_result.is_error():
                    validation_results["email_check"] = email_result.value.email_check.value
            
            # Execute signature validation
            if data_availability["signature_data"]:
                signature_result = await self._execute_signature_validation(contract_data)
                if not signature_result.is_error():
                    validation_results["signature_check"] = signature_result.value.signature_check.value
            
            # Execute bank validation
            if data_availability["bank_data"]:
                bank_result = await self._execute_bank_validation(contract_data)
                if not bank_result.is_error():
                    validation_results["bank_check"] = bank_result.value.bank_check.value
            
            # Execute VLP validation
            if data_availability["vlp_data"]:
                vlp_result = await self._execute_vlp_validation(contract_data)
                if not vlp_result.is_error():
                    validation_results.update({
                        "name_check": vlp_result.value.name_check.value,
                        "ssn_check": vlp_result.value.ssn_check.value,
                        "dob_check": vlp_result.value.dob_check.value,
                        "fees_check": vlp_result.value.fees_check.value,
                        "plan_check": vlp_result.value.plan_check.value
                    })
            
            # Execute gateway validation
            if data_availability["gateway_data"]:
                gateway_result = await self._execute_gateway_validation(contract_data)
                if not gateway_result.is_error():
                    validation_results.update({
                        "gateway_signature_check": gateway_result.value.gateway_signature_check.value,
                        "payment_count_check": gateway_result.value.payment_count_check.value,
                        "payment_amounts_check": gateway_result.value.payment_amounts_check.value,
                        "payment_dates_check": gateway_result.value.payment_dates_check.value
                    })
            
            # Execute SSN validation
            if data_availability["ssn_data"]:
                ssn_result = await self._execute_ssn_validation(contract_data)
                if not ssn_result.is_error():
                    validation_results["ssn_check"] = ssn_result.value.ssn_check.value
            
            # Execute DOB validation
            if data_availability["dob_data"]:
                dob_result = await self._execute_dob_validation(contract_data)
                if not dob_result.is_error():
                    validation_results.update({
                        "dob_check": dob_result.value.dob_check.value,
                        "age_plus_18_check": dob_result.value.age_plus_18_check.value
                    })
            
            # Execute debts validation
            if data_availability["debts_data"]:
                debts_result = await self._execute_debts_validation(contract_data)
                if not debts_result.is_error():
                    validation_results["debt_count_check"] = debts_result.value.debt_count_check.value
            
            # Determine overall result
            checks = list(validation_results.values())
            result, reason = ContractDataAnalyzer.determine_overall_result(checks)
            
            # Create analysis
            analysis = self._create_analysis(contract_data, validation_results, result, reason)
            
            masked_id = mask_contact_id(contact_id)
            logger.info(f"Contract validation orchestration completed for contact {masked_id}: {result.value}")
            return Success(analysis)
            
        except Exception as e:
            logger.error(f"Error orchestrating contract validations: {e}")
            return Error(f"Orchestration failed: {str(e)}")
    
    def _initialize_validation_results(self) -> Dict[str, str]:
        """Initialize validation results with default values."""
        return {
            "ip_check": "Missing Value",
            "email_check": "Missing Value",
            "signature_check": "Missing Value",
            "bank_check": "Missing Value",
            "name_check": "Missing Value",
            "ssn_check": "Missing Value",
            "dob_check": "Missing Value",
            "fees_check": "Missing Value",
            "plan_check": "Missing Value",
            "gateway_signature_check": "Missing Value",
            "payment_count_check": "Missing Value",
            "payment_amounts_check": "Missing Value",
            "payment_dates_check": "Missing Value",
            "age_plus_18_check": "Missing Value",
            "debt_count_check": "Missing Value"
        }
    
    def _create_no_data_analysis(self, contract_data: ContractDataIn) -> ContractAnalysis:
        """Create analysis for case when no data is available."""
        return ContractAnalysis(
            result=ContractValidity.NO_DATA,
            reason="No contract data available for analysis",
            ip_check="Missing Value",
            email_check="Missing Value",
            signature_check="Missing Value",
            bank_check="Missing Value",
            sender_ip_address=contract_data.sender_ip_address,
            signer_ip_address=contract_data.signer_ip_address,
            forth_email=contract_data.forth_email,
            contract_email=contract_data.contract_email,
            client_signature=contract_data.client_signature,
            coclient_signature=contract_data.coclient_signature,
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
        )
    
    def _create_analysis(self, contract_data: ContractDataIn, validation_results: Dict[str, str], 
                        result: ContractValidity, reason: str) -> ContractAnalysis:
        """Create the final analysis object with validation results embedded in the data."""
        return ContractAnalysis(
            result=result,
            reason=reason,
            # IP validation data and result
            sender_ip_address=contract_data.sender_ip_address,
            signer_ip_address=contract_data.signer_ip_address,
            ip_address_validation=validation_results["ip_check"],
            # Email validation data and result
            forth_email=contract_data.forth_email,
            contract_email=contract_data.contract_email,
            email_address_validation=validation_results["email_check"],
            # Signature validation data and result
            client_signature=contract_data.client_signature,
            coclient_signature=contract_data.coclient_signature,
            signature_validation=validation_results["signature_check"],
            # Bank validation data and result
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
            bank_account_validation=validation_results["bank_check"],
            # VLP validation data and results
            legal_plan_provider=contract_data.legal_plan_provider,
            vlp_client_signature=contract_data.vlp_client_signature,
            vlp_signature_date=contract_data.vlp_signature_date,
            contract_name=contract_data.contract_name,
            forth_name=contract_data.forth_name,
            contract_ssn=contract_data.contract_ssn,
            forth_ssn=contract_data.forth_ssn,
            legal_setup_fee_snapshot=contract_data.legal_setup_fee_snapshot,
            legal_monthly_fee_snapshot=contract_data.legal_monthly_fee_snapshot,
            legal_setup_fee_enrollment=contract_data.legal_setup_fee_enrollment,
            legal_monthly_fee_enrollment=contract_data.legal_monthly_fee_enrollment,
            payment_date=contract_data.payment_date,
            plan_name=contract_data.plan_name,
            vlp_name_validation=validation_results["name_check"],
            vlp_fees_validation=validation_results["fees_check"],
            vlp_plan_validation=validation_results["plan_check"],
            # Gateway validation data and results
            gateway_client_signature=contract_data.gateway_client_signature,
            contract_payment_count=contract_data.contract_payment_count,
            forth_payment_count=contract_data.forth_payment_count,
            payment_details=contract_data.payment_details,
            gateway_signature_validation=validation_results["gateway_signature_check"],
            payment_count_validation=validation_results["payment_count_check"],
            payment_amounts_validation=validation_results["payment_amounts_check"],
            payment_dates_validation=validation_results["payment_dates_check"],
            # SSN validation data and result
            payment_gateway_agreement_client_ssn=contract_data.payment_gateway_agreement_client_ssn,
            legal_plan_agreement_client_ssn=contract_data.legal_plan_agreement_client_ssn,
            power_of_attorney_client_ssn=contract_data.power_of_attorney_client_ssn,
            credit_report_ssn=contract_data.credit_report_ssn,
            ssn_consistency_validation=validation_results["ssn_check"],
            # DOB validation data and results
            forth_dob=contract_data.forth_dob,
            contract_dob=contract_data.contract_dob,
            dob_consistency_validation=validation_results["dob_check"],
            age_eligibility_validation=validation_results["age_plus_18_check"],
            # Debts validation data and result
            forth_debt_count=contract_data.forth_debt_count,
            contract_debt_count=contract_data.contract_debt_count,
            debt_count_validation=validation_results["debt_count_check"]
        )
    
    async def _execute_ip_validation(self, contract_data: ContractDataIn):
        """Execute IP validation."""
        ip_data = IPValidationDataIn(
            contact_id=contract_data.contact_id,
            sender_ip_address=contract_data.sender_ip_address,
            signer_ip_address=contract_data.signer_ip_address
        )
        return await self.ip_service.analyze_ip_validity(ip_data)
    
    async def _execute_email_validation(self, contract_data: ContractDataIn):
        """Execute email validation."""
        email_data = EmailValidationDataIn(
            contact_id=contract_data.contact_id,
            forth_email=contract_data.forth_email,
            contract_email=contract_data.contract_email
        )
        return await self.email_service.analyze_email_validity(email_data)
    
    async def _execute_signature_validation(self, contract_data: ContractDataIn):
        """Execute signature validation."""
        signature_data = SignatureValidationDataIn(
            contact_id=contract_data.contact_id,
            client_signature=contract_data.client_signature,
            coclient_signature=contract_data.coclient_signature
        )
        return await self.signature_service.analyze_signature_validity(signature_data)
    
    async def _execute_bank_validation(self, contract_data: ContractDataIn):
        """Execute bank validation."""
        bank_data = BankValidationDataIn(
            contact_id=contract_data.contact_id,
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
        )
        return await self.bank_service.analyze_bank_validity(bank_data)
    
    async def _execute_vlp_validation(self, contract_data: ContractDataIn):
        """Execute VLP validation."""
        vlp_data = VLPValidationDataIn(
            contact_id=contract_data.contact_id,
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
            plan_name=contract_data.plan_name
        )
        return await self.vlp_service.analyze_vlp_validity(vlp_data)
    
    async def _execute_gateway_validation(self, contract_data: ContractDataIn):
        """Execute gateway validation."""
        gateway_data = GatewayValidationDataIn(
            contact_id=contract_data.contact_id,
            gateway_client_signature=contract_data.gateway_client_signature,
            contract_payment_count=contract_data.contract_payment_count,
            forth_payment_count=contract_data.forth_payment_count,
            payment_details=contract_data.payment_details
        )
        return await self.gateway_service.analyze_gateway_validity(gateway_data)
    
    async def _execute_ssn_validation(self, contract_data: ContractDataIn):
        """Execute SSN validation."""
        ssn_data = SSNValidationDataIn(
            contact_id=contract_data.contact_id,
            payment_gateway_agreement_client_ssn=contract_data.payment_gateway_agreement_client_ssn,
            legal_plan_agreement_client_ssn=contract_data.legal_plan_agreement_client_ssn,
            power_of_attorney_client_ssn=contract_data.power_of_attorney_client_ssn,
            credit_report_ssn=contract_data.credit_report_ssn
        )
        return await self.ssn_service.analyze_ssn_validity(ssn_data)
    
    async def _execute_dob_validation(self, contract_data: ContractDataIn):
        """Execute DOB validation."""
        dob_data = DOBValidationDataIn(
            contact_id=contract_data.contact_id,
            forth_dob=contract_data.forth_dob,
            contract_dob=contract_data.contract_dob,
            age_plus_18_check=contract_data.age_plus_18_check
        )
        return await self.dob_service.analyze_dob_validity(dob_data)
    
    async def _execute_debts_validation(self, contract_data: ContractDataIn):
        """Execute debts validation."""
        debts_data = DebtsValidationDataIn(
            contact_id=contract_data.contact_id,
            forth_debt_count=contract_data.forth_debt_count,
            contract_debt_count=contract_data.contract_debt_count
        )
        return await self.debts_service.analyze_debts_validity(debts_data)

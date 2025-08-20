"""
Analysis Orchestrator for Combined Validation Service

This module handles parallel LLM analysis calls for all validation types.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from underwriting_validation.services.hardship_validation_service import HardshipValidationService
from underwriting_validation.services.budget_validation_service import BudgetValidationService, BudgetDataIn
from underwriting_validation.services.address_validation_service import AddressValidationService, AddressDataIn
from underwriting_validation.services.contract_validation_service import ContractValidationService, ContractDataIn
from underwriting_validation.services.duplication_validation_service import DuplicationValidationService, DuplicationDataIn
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    """Handles parallel LLM analysis for validation services."""
    
    def __init__(
        self, 
        hardship_service: HardshipValidationService,
        budget_service: BudgetValidationService,
        address_service: AddressValidationService,
        contract_service: ContractValidationService,
        duplication_service: DuplicationValidationService
    ):
        self.hardship_service = hardship_service
        self.budget_service = budget_service
        self.address_service = address_service
        self.contract_service = contract_service
        self.duplication_service = duplication_service
    
    async def run_parallel_analyses(
        self,
        contact_id: int,
        hardship_data: Optional[Dict[str, Any]],
        budget_data: Optional[Dict[str, Any]],
        address_data: Optional[Dict[str, Any]],
        contract_data: Optional[Dict[str, Any]],
        duplication_data: Optional[Dict[str, Any]],
        data_availability: Dict[str, bool]
    ) -> Tuple[Any, Any, Any, Any, Any]:
        """
        Run all LLM analyses in parallel.
        
        Args:
            contact_id: The contact ID being analyzed
            hardship_data: Hardship data
            budget_data: Budget data
            address_data: Address data
            contract_data: Contract data
            duplication_data: Duplication data
            data_availability: Dictionary indicating which data types are available
            
        Returns:
            Tuple of analysis results (hardship, budget, address, contract, duplication)
        """
        masked_id = mask_contact_id(contact_id)
        
        # Prepare LLM analysis tasks for parallel execution
        analysis_tasks = []
        analysis_task_names = []
        
        # Prepare hardship analysis if data exists
        if data_availability.get('hardship'):
            analysis_tasks.append(self.hardship_service.analyze_hardship_validity(hardship_data))
            analysis_task_names.append('hardship')
        
        # Prepare budget analysis if data exists
        if data_availability.get('budget'):
            budget_data_model = BudgetDataIn(
                contact_id=budget_data['contact_id'],
                total_net_income=budget_data['total_net_income'],
                total_expenses=budget_data['total_expenses']
            )
            analysis_tasks.append(self.budget_service.analyze_budget_validity(budget_data_model))
            analysis_task_names.append('budget')
        
        # Prepare address analysis if data exists
        if data_availability.get('address'):
            address_data_model = AddressDataIn(
                contact_id=address_data['contact_id'],
                state=address_data.get('state'),
                assigned_company=address_data.get('assigned_company')
            )
            analysis_tasks.append(self.address_service.analyze_address_validity(address_data_model))
            analysis_task_names.append('address')
        
        # Prepare contract analysis if data exists
        if data_availability.get('contract'):
            contract_data_model = ContractDataIn(
                contact_id=contract_data['contact_id'],
                sender_ip_address=contract_data.get('sender_ip_address'),
                signer_ip_address=contract_data.get('signer_ip_address'),
                forth_email=contract_data.get('forth_email'),
                contract_email=contract_data.get('contract_email'),
                client_signature=contract_data.get('client_signature'),
                client_signature_date=contract_data.get('client_signature_date'),
                coclient_signature=contract_data.get('coclient_signature'),
                coclient_signature_date=contract_data.get('coclient_signature_date'),
                # Bank details
                contract_account_number=contract_data.get('contract_account_number'),
                forth_account_number=contract_data.get('forth_account_number'),
                contract_routing_number=contract_data.get('contract_routing_number'),
                forth_routing_number=contract_data.get('forth_routing_number'),
                contract_bank_name=contract_data.get('contract_bank_name'),
                forth_bank_name=contract_data.get('forth_bank_name'),
                contract_account_type=contract_data.get('contract_account_type'),
                forth_account_type=contract_data.get('forth_account_type'),
                contract_address=contract_data.get('contract_address'),
                forth_address=contract_data.get('forth_address'),
                # SSN validation fields
                payment_gateway_agreement_client_ssn=contract_data.get('payment_gateway_agreement_client_ssn'),
                legal_plan_agreement_client_ssn=contract_data.get('legal_plan_agreement_client_ssn'),
                power_of_attorney_client_ssn=contract_data.get('power_of_attorney_client_ssn'),
                credit_report_ssn=contract_data.get('credit_report_ssn'),
                ssn_check=contract_data.get('ssn_check'),
                # DOB validation fields
                forth_dob=contract_data.get('forth_dob'),
                contract_dob=contract_data.get('contract_dob'),
                dob_check=contract_data.get('dob_check'),
                age_plus_18_check=contract_data.get('age_plus_18_check'),
                # Debts validation fields
                forth_debt_count=contract_data.get('forth_debt_count'),
                contract_debt_count=contract_data.get('contract_debt_count'),
                debt_count_check=contract_data.get('debt_count_check')
            )
            analysis_tasks.append(self.contract_service.analyze_contract_validity(contract_data_model))
            analysis_task_names.append('contract')
        
        # Prepare duplication analysis if data exists
        if data_availability.get('duplication'):
            duplication_data_model = DuplicationDataIn(
                contact_id=duplication_data['contact_id'],
                ssn=duplication_data.get('ssn'),
                phone=duplication_data.get('phone')
            )
            analysis_tasks.append(self.duplication_service.analyze_duplication_validity(duplication_data_model))
            analysis_task_names.append('duplication')
        
        # Execute all LLM analyses in parallel
        logger.info(f"Running {len(analysis_tasks)} LLM analyses for contact {masked_id} in parallel...")
        analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Process analysis results
        hardship_analysis = None
        budget_analysis = None
        address_analysis = None
        contract_analysis = None
        duplication_analysis = None
        
        # Process each analysis result
        for i, (result, task_name) in enumerate(zip(analysis_results, analysis_task_names)):
            if isinstance(result, Exception):
                logger.error(f"{task_name.capitalize()} analysis failed for contact {masked_id}: {result}")
                continue
            
            if result.is_error():
                logger.error(f"{task_name.capitalize()} analysis failed for contact {masked_id}: {result.error}")
                continue
            
            # Process successful results
            if task_name == 'hardship':
                hardship_analysis = result.value
                logger.info(f"Hardship analysis for contact {masked_id}: result={hardship_analysis.result.value}, confidence={hardship_analysis.confidence}")
            
            elif task_name == 'budget':
                budget_analysis = result.value
                logger.info(f"Budget analysis for contact {masked_id}: result={budget_analysis.result.value}, surplus={budget_analysis.surplus_indication}, difference=${budget_analysis.surplus:,.2f}")
            
            elif task_name == 'address':
                address_analysis = result.value
                logger.info(f"Address analysis for contact {masked_id}: result={address_analysis.result.value}, state_check={address_analysis.state_check}")
            
            elif task_name == 'contract':
                contract_analysis = result.value
                logger.info(f"Contract analysis for contact {masked_id}: result={contract_analysis.result.value}, ip_address_validation={contract_analysis.ip_address_validation}, email_address_validation={contract_analysis.email_address_validation}, signature_validation={contract_analysis.signature_validation}, bank_account_validation={contract_analysis.bank_account_validation}")
            
            elif task_name == 'duplication':
                duplication_analysis = result.value
                logger.info(f"Duplication analysis for contact {masked_id}: result={duplication_analysis.result}, has_duplicates={duplication_analysis.has_duplicates}")
        
        logger.info(f"LLM analysis completed for contact {masked_id}")
        
        return hardship_analysis, budget_analysis, address_analysis, contract_analysis, duplication_analysis

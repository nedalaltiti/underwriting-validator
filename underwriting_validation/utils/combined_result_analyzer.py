"""
Combined Result Analyzer for Underwriting Validation

This module provides logic to analyze combined validation results from hardship,
budget, and address validations and determine the overall result with detailed reasoning.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Represents a single validation result."""
    type: str  # 'hardship', 'budget', 'address'
    result: str  # 'pass', 'no_pass', 'mixed', 'no_data'
    confidence: Optional[float] = None
    reason: Optional[str] = None


class CombinedResultAnalyzer:
    """Analyzes combined validation results and provides detailed reasoning."""
    
    def __init__(self):
        """Initialize the combined result analyzer."""
        pass
    
    def analyze_combined_result(
        self,
        hardship_analysis: Optional[Dict[str, Any]] = None,
        budget_analysis: Optional[Dict[str, Any]] = None,
        address_analysis: Optional[Dict[str, Any]] = None,
        contract_analysis: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """
        Analyze combined validation results and determine overall result with reasoning.
        
        Args:
            hardship_analysis: Hardship validation analysis data
            budget_analysis: Budget validation analysis data
            address_analysis: Address validation analysis data
            contract_analysis: Contract validation analysis data
            
        Returns:
            Tuple of (combined_result, combined_result_reason)
        """
        # Convert to ValidationResult objects
        hardship_result = self._extract_validation_result('hardship', hardship_analysis)
        budget_result = self._extract_validation_result('budget', budget_analysis)
        address_result = self._extract_validation_result('address', address_analysis)
        contract_result = self._extract_validation_result('contract', contract_analysis)
        
        # Get available validations
        available_validations = [r for r in [hardship_result, budget_result, address_result, contract_result] if r is not None]
        
        # If no data for any validation
        if not available_validations:
            return "no_data", "No validation data available for any category (hardship, budget, address, or contract)"
        
        # Check if any validation returned "not_eligible"
        not_eligible_validations = [v for v in available_validations if v.result == "not_eligible"]
        if not_eligible_validations:
            return "not_eligible", "Contact is not eligible for validation process"
        
        # If only one validation available
        if len(available_validations) == 1:
            validation = available_validations[0]
            if validation.result == "pass":
                return "pass", f"Only {validation.type} validation available and it passed"
            elif validation.result == "no_pass":
                return "no_pass", f"Only {validation.type} validation available and it failed"
            elif validation.result == "mixed":
                return "mixed", f"Only {validation.type} validation available with mixed results"
            else:
                return "no_data", f"Only {validation.type} validation available but no data"
        
        # Multiple validations available - analyze combinations
        return self._analyze_multiple_validations(available_validations)
    
    def _extract_validation_result(self, validation_type: str, analysis_data: Optional[Dict[str, Any]]) -> Optional[ValidationResult]:
        """Extract validation result from analysis data."""
        if not analysis_data:
            return ValidationResult(
                type=validation_type,
                result="no_data",
                reason=f"No {validation_type} data available"
            )
        
        if validation_type == "hardship":
            result = analysis_data.get('hardship_validation_result', 'no_data')
            confidence = analysis_data.get('hardship_validation_analysis')
            if result == "no_data":
                return ValidationResult(
                    type="hardship",
                    result="no_data",
                    reason="No hardship data available"
                )
            return ValidationResult(
                type="hardship",
                result=result,
                confidence=confidence,
                reason=confidence
            )
        elif validation_type == "budget":
            result = analysis_data.get('budget_outcome', 'no_data')
            difference = analysis_data.get('budget_difference', 0)
            surplus_indication = analysis_data.get('surplus_indication', 'unknown')
            if result == "no_data":
                return ValidationResult(
                    type="budget",
                    result="no_data",
                    reason="No budget data available"
                )
            return ValidationResult(
                type="budget",
                result=result,
                reason=f"Budget {surplus_indication} surplus: ${difference:,.2f}" if difference else "No budget data"
            )
        elif validation_type == "address":
            result = analysis_data.get('address_validation_result', 'no_data')
            state_check = analysis_data.get('state_check', 'Unknown')
            assigned_company = analysis_data.get('assigned_company', 'Unknown')
            if result == "no_data":
                return ValidationResult(
                    type="address",
                    result="no_data",
                    reason="No address data available"
                )
            return ValidationResult(
                type="address",
                result=result,
                reason=f"State: {state_check}, Company: {assigned_company}"
            )
        elif validation_type == "contract":
            result = analysis_data.get('contract_validation_result', 'no_data')
            ip_check = analysis_data.get('ip_check', 'Unknown')
            email_check = analysis_data.get('email_check', 'Unknown')
            signature_check = analysis_data.get('signature_check', 'Unknown')
            bank_check = analysis_data.get('bank_check', 'Unknown')
            name_check = analysis_data.get('name_check', 'Unknown')
            ssn_check = analysis_data.get('ssn_check', 'Unknown')
            dob_check = analysis_data.get('dob_check', 'Unknown')
            fees_check = analysis_data.get('fees_check', 'Unknown')
            plan_check = analysis_data.get('plan_check', 'Unknown')
            gateway_signature_check = analysis_data.get('gateway_signature_check', 'Unknown')
            payment_count_check = analysis_data.get('payment_count_check', 'Unknown')
            payment_amounts_check = analysis_data.get('payment_amounts_check', 'Unknown')
            payment_dates_check = analysis_data.get('payment_dates_check', 'Unknown')
            if result == "no_data":
                return ValidationResult(
                    type="contract",
                    result="no_data",
                    reason="No contract data available"
                )
            return ValidationResult(
                type="contract",
                result=result,
                reason=f"IP: {ip_check}, Email: {email_check}, Signature: {signature_check}, Bank: {bank_check}, VLP Name: {name_check}, VLP SSN: {ssn_check}, VLP DOB: {dob_check}, VLP Fees: {fees_check}, VLP Plan: {plan_check}, Gateway Sig: {gateway_signature_check}, Payment Count: {payment_count_check}, Payment Amounts: {payment_amounts_check}, Payment Dates: {payment_dates_check}"
            )
        
        return None
    
    def _analyze_multiple_validations(self, validations: list[ValidationResult]) -> tuple[str, str]:
        """Analyze multiple validation results and determine combined outcome."""
        # Count results
        pass_count = sum(1 for v in validations if v.result == "pass")
        no_pass_count = sum(1 for v in validations if v.result == "no_pass")
        mixed_count = sum(1 for v in validations if v.result == "mixed")
        no_data_count = sum(1 for v in validations if v.result == "no_data")
        total_count = len(validations)
        
        # Determine combined result and reason
        if pass_count == total_count:
            # All validations pass
            validation_types = [v.type for v in validations]
            return "pass", f"All validations passed: {', '.join(validation_types)}"
        
        elif no_pass_count == total_count:
            # All validations fail
            validation_types = [v.type for v in validations]
            return "no_pass", f"All validations failed: {', '.join(validation_types)}"
        
        elif pass_count > no_pass_count and pass_count >= 2:
            # Majority pass (at least 2 out of 3)
            passing_types = [v.type for v in validations if v.result == "pass"]
            failing_types = [v.type for v in validations if v.result == "no_pass"]
            no_data_types = [v.type for v in validations if v.result == "no_data"]
            
            reason_parts = [f"Majority passed ({', '.join(passing_types)})"]
            if failing_types:
                reason_parts.append(f"Failed: {', '.join(failing_types)}")
            if no_data_types:
                reason_parts.append(f"No data: {', '.join(no_data_types)}")
            
            return "pass", f"{'; '.join(reason_parts)}"
        
        elif no_pass_count > pass_count and no_pass_count >= 2:
            # Majority fail (at least 2 out of 3)
            failing_types = [v.type for v in validations if v.result == "no_pass"]
            passing_types = [v.type for v in validations if v.result == "pass"]
            no_data_types = [v.type for v in validations if v.result == "no_data"]
            
            reason_parts = [f"Majority failed ({', '.join(failing_types)})"]
            if passing_types:
                reason_parts.append(f"Passed: {', '.join(passing_types)}")
            if no_data_types:
                reason_parts.append(f"No data: {', '.join(no_data_types)}")
            
            return "no_pass", f"{'; '.join(reason_parts)}"
        
        elif mixed_count > 0:
            # Mixed results present
            mixed_types = [v.type for v in validations if v.result == "mixed"]
            pass_types = [v.type for v in validations if v.result == "pass"]
            fail_types = [v.type for v in validations if v.result == "no_pass"]
            no_data_types = [v.type for v in validations if v.result == "no_data"]
            
            reason_parts = []
            if pass_types:
                reason_parts.append(f"Passed: {', '.join(pass_types)}")
            if fail_types:
                reason_parts.append(f"Failed: {', '.join(fail_types)}")
            if mixed_types:
                reason_parts.append(f"Mixed: {', '.join(mixed_types)}")
            if no_data_types:
                reason_parts.append(f"No data: {', '.join(no_data_types)}")
            
            return "mixed", f"Mixed validation results - {'; '.join(reason_parts)}"
        
        elif no_data_count > 0:
            # Some validations have no data
            no_data_types = [v.type for v in validations if v.result == "no_data"]
            pass_types = [v.type for v in validations if v.result == "pass"]
            fail_types = [v.type for v in validations if v.result == "no_pass"]
            
            reason_parts = []
            if pass_types:
                reason_parts.append(f"Passed: {', '.join(pass_types)}")
            if fail_types:
                reason_parts.append(f"Failed: {', '.join(fail_types)}")
            if no_data_types:
                reason_parts.append(f"No data: {', '.join(no_data_types)}")
            
            if not pass_types and not fail_types:
                return "no_data", f"No data available for any validation: {', '.join(no_data_types)}"
            else:
                return "mixed", f"Limited data available - {'; '.join(reason_parts)}"
        
        else:
            # Edge case - equal pass/fail counts
            pass_types = [v.type for v in validations if v.result == "pass"]
            fail_types = [v.type for v in validations if v.result == "no_pass"]
            no_data_types = [v.type for v in validations if v.result == "no_data"]
            
            reason_parts = [f"Equal pass/fail results - Passed: {', '.join(pass_types)}; Failed: {', '.join(fail_types)}"]
            if no_data_types:
                reason_parts.append(f"No data: {', '.join(no_data_types)}")
            
            return "mixed", f"{'; '.join(reason_parts)}"

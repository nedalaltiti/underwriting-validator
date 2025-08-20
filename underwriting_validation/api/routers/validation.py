"""
Validation API Router

This module provides pure API endpoints for contact validation,
removing all Teams and feedback-related functionality.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from underwriting_validation.utils.di import get_contact_validation_uc, get_combined_validation_uc
from underwriting_validation.services.contact_service import ContactService, InvalidContactIDError, ContactNotFoundError
from underwriting_validation.services.combined_validation_service import CombinedValidationService
from underwriting_validation.utils.pii_filter import mask_contact_id
from underwriting_validation.utils.rate_limiter import RateLimiter, limiter

logger = logging.getLogger(__name__)
router = APIRouter()

# API Models
class ContactValidationRequest(BaseModel):
    """Request model for contact validation."""
    contact_id: int = Field(ge=1, le=10**11, description="Contact ID to validate (must be a positive integer, supports up to 11 digits)")
    include_budget: bool = Field(default=True, description="Include budget validation")
    include_hardship: bool = Field(default=True, description="Include hardship validation")
    include_address: bool = Field(default=True, description="Include address validation")

class ContactValidationResponse(BaseModel):
    """Response model for contact validation."""
    contact_id: int
    success: bool
    message: str
    validation_type: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class CombinedValidationRequest(BaseModel):
    """Request model for combined validation."""
    contact_id: int = Field(ge=1, le=10**11, description="Contact ID to validate (must be a positive integer, supports up to 11 digits)")

class CombinedValidationResponse(BaseModel):
    """Response model for combined validation."""
    contact_id: int
    eligibility: str
    success: bool
    combined_result: str
    combined_result_reason: Optional[str] = None
    message: str
    eligibility_data: Optional[Dict[str, Any]] = None
    hardship_data: Optional[Dict[str, Any]] = None
    budget_data: Optional[Dict[str, Any]] = None
    address_data: Optional[Dict[str, Any]] = None
    contract_data: Optional[Dict[str, Any]] = None
    duplication_data: Optional[Dict[str, Any]] = None
    draft_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/contact", 
    response_model=ContactValidationResponse
)
@limiter.limit("5/60s")
async def validate_contact(
    request: Request,
    req: ContactValidationRequest,
    contact_service: ContactService = Depends(get_contact_validation_uc)
):
    """
    Validate a contact for hardship, budget, and/or address information.
    
    This endpoint provides a robust validation of a contact's hardship, budget, and address data.
    """
    try:
        masked_id = mask_contact_id(req.contact_id)
        logger.info(f"Validating contact {masked_id}")
        
        # Contact ID validation is handled by the service methods
        # They will raise InvalidContactIDError or ContactNotFoundError as appropriate
        
        # Get contact data based on requested validation types
        hardship_data = None
        budget_data = None
        address_data = None
        
        if req.include_hardship:
            hardship_data = await contact_service.analyze_contact_hardship(req.contact_id)
        
        if req.include_budget:
            budget_data = await contact_service.get_contact_budget_analysis(req.contact_id)
        
        if req.include_address:
            address_data = await contact_service.analyze_contact_address(req.contact_id)
        
        # Combine the data
        contact_data = hardship_data or budget_data or address_data
        
        if not contact_data:
            return ContactValidationResponse(
                contact_id=req.contact_id,
                success=False,
                message="No data found for this contact",
                validation_type="contact",
                data=None,
                error="No contact data available"
            )
        
        # Format the response based on what data we have
        response_parts = []
        combined_data = {}
        
        if hardship_data:
            response_parts.append(contact_service.format_contact_response(hardship_data))
            combined_data["hardship"] = hardship_data
        
        if budget_data:
            response_parts.append(contact_service.format_budget_response(budget_data))
            combined_data["budget"] = budget_data
        
        if address_data:
            response_parts.append(contact_service.format_address_response(address_data))
            combined_data["address"] = address_data
        
        if not response_parts:
            formatted_response = "No validation data available for this contact"
            combined_data = None
        else:
            formatted_response = "\n\n".join(response_parts)
        
        return ContactValidationResponse(
            contact_id=req.contact_id,
            success=True,
            message=formatted_response,
            validation_type="contact",
            data=combined_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        masked_id = mask_contact_id(req.contact_id)
        logger.error(f"Error validating contact {masked_id}: {e}")
        return ContactValidationResponse(
            contact_id=req.contact_id,
            success=False,
            message="An error occurred during validation",
            validation_type="contact",
            error=str(e)
        )

@router.post("/combined", 
    response_model=CombinedValidationResponse
)
@limiter.limit("5/60s")
async def validate_contact_combined(
    request: Request,
    req: CombinedValidationRequest,
    combined_service: CombinedValidationService = Depends(get_combined_validation_uc)
):
    """
    Perform combined hardship, budget, and address validation for a contact.
    
    This endpoint provides comprehensive validation combining hardship,
    budget, and address analysis in a single request.
        """
    try:
        masked_id = mask_contact_id(req.contact_id)
        logger.info(f"Performing combined validation for contact {masked_id}")
        
        # Perform combined validation
        result = await combined_service.perform_combined_validation(req.contact_id)
        
        if result:
            logger.info(f"Combined validation completed for contact {masked_id}: eligibility={result.get('eligibility')}, result={result.get('combined_result')}")
        else:
            logger.warning(f"No validation result returned for contact {masked_id}")
        
        if not result:
                    return CombinedValidationResponse(
            contact_id=req.contact_id,
            eligibility="not eligible",
            success=False,
            combined_result="no_data",
            combined_result_reason="No validation data available for any category",
            message="No data found for this contact",
            eligibility_data=None,
            hardship_data=None,
            budget_data=None,
            address_data=None,
            contract_data=None,
            duplication_data=None,
            draft_data=None,
            error="No contact data available"
        )
        
        return CombinedValidationResponse(
            contact_id=req.contact_id,
            eligibility=result.get("eligibility", "not eligible"),
            success=result.get("success", False),
            combined_result=result.get("combined_result", "error"),
            combined_result_reason=result.get("combined_result_reason"),
            message=result.get("message", "Validation completed"),
            eligibility_data=result.get("eligibility_data"),
            hardship_data=result.get("hardship_data"),
            budget_data=result.get("budget_data"),
            address_data=result.get("address_data"),
            contract_data=result.get("contract_data"),
            duplication_data=result.get("duplication_data"),
            draft_data=result.get("draft_data"),
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        masked_id = mask_contact_id(req.contact_id)
        logger.error(f"Error performing combined validation for contact {masked_id}: {e}")
        return CombinedValidationResponse(
            contact_id=req.contact_id,
            eligibility="not eligible",
            success=False,
            combined_result="error",
            combined_result_reason="Error occurred during validation analysis",
            message="An error occurred during combined validation",
            eligibility_data=None,
            hardship_data=None,
            budget_data=None,
            address_data=None,
            contract_data=None,
            duplication_data=None,
            draft_data=None,
            error=str(e)
        )



@router.get("/contact/{contact_id}")
async def get_contact_info(
    contact_id: int,
    contact_service: ContactService = Depends(get_contact_validation_uc)
):
    """
    Get basic contact information with hardship, budget, and address data availability.
    
    This endpoint provides basic contact lookup to check if hardship, budget, and address
    data are available for a contact, without performing validation analysis.
    """
    try:
        masked_id = mask_contact_id(contact_id)
        logger.info(f"Getting contact info for {masked_id}")
        
        # Contact ID validation is handled by the service methods
        # They will raise InvalidContactIDError or ContactNotFoundError as appropriate
        
        # Get raw hardship data (without analysis)
        hardship_data = await contact_service.get_contact_with_hardship_data(contact_id)
        
        # Get raw budget data (without analysis)
        budget_data = await contact_service.get_contact_with_budget_data(contact_id)
        
        # Get raw address data (without analysis)
        address_data = await contact_service.get_contact_with_address_data(contact_id)
        
        if not hardship_data and not budget_data and not address_data:
            raise HTTPException(
                status_code=404,
                detail=f"Contact {contact_id} not found"
            )
        
        # Check data availability
        has_hardship_data = hardship_data and any([
            hardship_data.get('financial_hardship'),
            hardship_data.get('hardship_description')
        ])
        
        has_budget_data = budget_data and any([
            budget_data.get('total_net_income', 0) > 0,
            budget_data.get('total_expenses', 0) > 0
        ])
        
        has_address_data = address_data and any([
            address_data.get('state'),
            address_data.get('assigned_company')
        ])
        
        return {
            "contact_id": contact_id,
            "success": True,
            "data_available": {
                "hardship": has_hardship_data,
                "budget": has_budget_data,
                "address": has_address_data
            },
            "hardship_data": hardship_data if has_hardship_data else None,
            "budget_data": budget_data if has_budget_data else None,
            "address_data": address_data if has_address_data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        masked_id = mask_contact_id(contact_id)
        logger.error(f"Error getting contact info for {masked_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving contact information: {str(e)}"
        )
"""
Validation API Router

This module provides pure API endpoints for contact validation,
removing all Teams and feedback-related functionality.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from underwriting_validation.utils.di import get_contact_validation_uc, get_combined_validation_uc
from underwriting_validation.services.contact_service import ContactService, InvalidContactIDError, ContactNotFoundError
from underwriting_validation.services.combined_validation_service import CombinedValidationService

logger = logging.getLogger(__name__)
router = APIRouter()

# API Models
class ContactValidationRequest(BaseModel):
    """Request model for contact validation."""
    contact_id: int = Field(ge=1, le=10**11, description="Contact ID to validate (must be a positive integer, supports up to 11 digits)")
    include_budget: bool = Field(default=True, description="Include budget validation")
    include_hardship: bool = Field(default=True, description="Include hardship validation")

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
    success: bool
    message: str
    hardship_data: Optional[Dict[str, Any]] = None
    budget_data: Optional[Dict[str, Any]] = None
    combined_result: Optional[str] = None
    error: Optional[str] = None

@router.post("/contact", response_model=ContactValidationResponse)
async def validate_contact(
    req: ContactValidationRequest,
    contact_service: ContactService = Depends(get_contact_validation_uc)
):
    """
    Validate a contact for hardship and/or budget information.
    
    This endpoint provides a robust validation of a contact's hardship and budget data.
    """
    try:
        logger.info(f"Validating contact {req.contact_id}")
        
        # Contact ID validation is handled by the service methods
        # They will raise InvalidContactIDError or ContactNotFoundError as appropriate
        
        # Get contact data based on requested validation types
        hardship_data = None
        budget_data = None
        
        if req.include_hardship:
            hardship_data = await contact_service.analyze_contact_hardship(req.contact_id)
        
        if req.include_budget:
            budget_data = await contact_service.get_contact_budget_analysis(req.contact_id)
        
        # Combine the data
        contact_data = hardship_data or budget_data
        
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
        if hardship_data and budget_data:
            # Both hardship and budget data available
            formatted_response = f"{contact_service.format_contact_response(hardship_data)}\n\n{contact_service.format_budget_response(budget_data)}"
            combined_data = {
                "hardship": hardship_data,
                "budget": budget_data
            }
        elif hardship_data:
            # Only hardship data
            formatted_response = contact_service.format_contact_response(hardship_data)
            combined_data = hardship_data
        elif budget_data:
            # Only budget data
            formatted_response = contact_service.format_budget_response(budget_data)
            combined_data = budget_data
        else:
            # No data
            formatted_response = "No validation data available for this contact"
            combined_data = None
        
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
        logger.error(f"Error validating contact {req.contact_id}: {e}")
        return ContactValidationResponse(
            contact_id=req.contact_id,
            success=False,
            message="An error occurred during validation",
            validation_type="contact",
            error=str(e)
        )

@router.post("/combined", response_model=CombinedValidationResponse)
async def validate_contact_combined(
    req: CombinedValidationRequest,
    combined_service: CombinedValidationService = Depends(get_combined_validation_uc)
):
    """
    Perform combined hardship and budget validation for a contact.
    
    This endpoint provides comprehensive validation combining both hardship
    and budget analysis in a single request.
    """
    try:
        logger.info(f"Performing combined validation for contact {req.contact_id}")
        
        # Perform combined validation
        result = await combined_service.perform_combined_validation(req.contact_id)
        
        if not result:
            return CombinedValidationResponse(
                contact_id=req.contact_id,
                success=False,
                message="No data found for this contact",
                hardship_data=None,
                budget_data=None,
                combined_result=None,
                error="No contact data available"
            )
        
        return CombinedValidationResponse(
            contact_id=req.contact_id,
            success=True,
            message=result.get("formatted_response", "Validation completed"),
            hardship_data=result.get("hardship_data"),
            budget_data=result.get("budget_data"),
            combined_result=result.get("combined_result")
        )
        
    except Exception as e:
        logger.error(f"Error performing combined validation for contact {req.contact_id}: {e}")
        return CombinedValidationResponse(
            contact_id=req.contact_id,
            success=False,
            message="An error occurred during combined validation",
            hardship_data=None,
            budget_data=None,
            combined_result=None,
            error=str(e)
        )

@router.get("/contact/{contact_id}")
async def get_contact_info(
    contact_id: int,
    contact_service: ContactService = Depends(get_contact_validation_uc)
):
    """
    Get basic contact information with hardship and budget data availability.
    
    This endpoint provides basic contact lookup to check if hardship and budget
    data are available for a contact, without performing validation analysis.
    """
    try:
        logger.info(f"Getting contact info for {contact_id}")
        
        # Contact ID validation is handled by the service methods
        # They will raise InvalidContactIDError or ContactNotFoundError as appropriate
        
        # Get raw hardship data (without analysis)
        hardship_data = await contact_service.get_contact_with_hardship_data(contact_id)
        
        # Get raw budget data (without analysis)
        budget_data = await contact_service.get_contact_with_budget_data(contact_id)
        
        if not hardship_data and not budget_data:
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
        
        return {
            "contact_id": contact_id,
            "success": True,
            "data_available": {
                "hardship": has_hardship_data,
                "budget": has_budget_data
            },
            "hardship_data": hardship_data if has_hardship_data else None,
            "budget_data": budget_data if has_budget_data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contact info for {contact_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving contact information: {str(e)}"
        ) 
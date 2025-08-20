from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
import time
import logging
from datetime import datetime
from underwriting_validation.utils.di import get_contact_validation_uc
from underwriting_validation.services.contact_service import InvalidContactIDError, ContactNotFoundError
from underwriting_validation.config.settings import settings
from underwriting_validation.utils.rate_limiter import RateLimiter


logger = logging.getLogger(__name__)
router = APIRouter()

# Debug endpoint models

class ContactQueryRequest(BaseModel):
    contact_id: int = Field(ge=1, le=10**11, description="Contact ID must be a positive integer (supports up to 11 digits)")
    user_id: str = "debug-user"

class ContactQueryResponse(BaseModel):
    contact_id: int
    contact_info: Optional[dict] = None
    response: str
    success: bool
    processing_time: float

@router.post("/contact", 
    response_model=ContactQueryResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]  # 5 requests/minute
)
async def debug_contact_query(
    req: ContactQueryRequest,
    contact_service = Depends(get_contact_validation_uc)
):
    """Debug endpoint for testing validation data check."""
    start_time = time.time()
    
    try:
        # Check hardship, budget, address, and credit score validation data
        hardship_result = await contact_service.analyze_contact_hardship(req.contact_id)
        budget_result = await contact_service.get_contact_budget_analysis(req.contact_id)
        address_result = await contact_service.analyze_contact_address(req.contact_id)
        credit_score_result = await contact_service.analyze_contact_credit_score(req.contact_id)
        
        # Combine responses
        response_parts = []
        
        if hardship_result:
            hardship_response = await contact_service.format_contact_response(hardship_result)
            response_parts.append("**HARDSHIP ANALYSIS:**")
            response_parts.append(hardship_response)
        
        if budget_result:
            budget_response = await contact_service.format_budget_response(budget_result)
            response_parts.append("**BUDGET ANALYSIS:**")
            response_parts.append(budget_response)
        
        if address_result:
            address_response = await contact_service.format_address_response(address_result)
            response_parts.append("**ADDRESS ANALYSIS:**")
            response_parts.append(address_response)
        
        if credit_score_result:
            credit_score_response = await contact_service.format_credit_score_response(credit_score_result)
            response_parts.append("**CREDIT SCORE ANALYSIS:**")
            response_parts.append(credit_score_response)
        
        if not hardship_result and not budget_result and not address_result and not credit_score_result:
            response_parts.append("No hardship, budget, address, or credit score data found for this contact.")
        
        combined_response = "\n\n".join(response_parts)
        
        # Combine the data for the response
        combined_data = {
            "hardship": hardship_result,
            "budget": budget_result,
            "address": address_result,
            "credit_score": credit_score_result
        }
        
        processing_time = time.time() - start_time
        
        return ContactQueryResponse(
            contact_id=req.contact_id,
            contact_info=combined_data,
            response=combined_response,
            success=hardship_result is not None or budget_result is not None or address_result is not None or credit_score_result is not None,
            processing_time=round(processing_time, 2)
        )
        
    except (InvalidContactIDError, ContactNotFoundError) as e:
        # Let the global exception handlers deal with these
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in debug contact query: {e}")
        processing_time = time.time() - start_time
        return ContactQueryResponse(
            contact_id=req.contact_id,
            contact_info=None,
            response=f"Error processing request: {str(e)}",
            success=False,
            processing_time=round(processing_time, 2)
        )



 
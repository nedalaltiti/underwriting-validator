"""
Rate limiting utilities for the Underwriting Validation API.

This module provides a simple rate limiter implementation using slowapi.
"""

import logging
from typing import Optional
from fastapi import HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# Create a global limiter instance
limiter = Limiter(key_func=get_remote_address)

def RateLimiter(times: int, seconds: int):
    """
    Create a rate limiter dependency for FastAPI endpoints.
    
    Args:
        times: Number of requests allowed
        seconds: Time window in seconds
        
    Returns:
        A dependency function that can be used with FastAPI's Depends()
    """
    @limiter.limit(f"{times}/{seconds}s")
    def rate_limit_dependency(request):
        """Rate limiting dependency that raises HTTPException when limit exceeded."""
        return None
    
    return rate_limit_dependency

def get_rate_limiter():
    """Get the global limiter instance for use in the FastAPI app."""
    return limiter 
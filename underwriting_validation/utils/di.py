from functools import lru_cache
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from underwriting_validation.services.gemini_service import GeminiService
from underwriting_validation.services.contact_service import ContactService
from underwriting_validation.services.hardship_validation_service import HardshipValidationService
from underwriting_validation.services.budget_validation_service import BudgetValidationService
from underwriting_validation.services.combined_validation_service import CombinedValidationService
from underwriting_validation.db.session import get_db_session

"""
Dependency-provider helpers for FastAPI.

Each object is created lazily once per process and can be overridden
in tests with FastAPI's dependency-override mechanism.

Underwriting is focused on validation only.
"""

@lru_cache
def get_llm() -> GeminiService:
    """Return a shared GeminiService instance for validation analysis."""
    return GeminiService()


@lru_cache
def get_hardship_service() -> HardshipValidationService:
    """Return a shared HardshipValidationService instance."""
    return HardshipValidationService()


@lru_cache
def get_budget_service() -> BudgetValidationService:
    """Return a shared BudgetValidationService instance."""
    return BudgetValidationService()


@lru_cache
def get_combined_validation_service() -> CombinedValidationService:
    """Return a shared CombinedValidationService instance."""
    hardship_service = get_hardship_service()
    budget_service = get_budget_service()
    # Note: This will need to be updated to use dependency injection with session
    from underwriting_validation.infrastructure.contact_repository import ContactRepository
    # For now, we'll create a temporary repository - this should be updated
    # to use proper dependency injection with session
    return CombinedValidationService(hardship_service, budget_service, None)


def get_contact_service_with_session(session) -> ContactService:
    """
    Return a ContactService with the provided database session.
    
    This is the proper dependency injection pattern where the session
    is passed in from the FastAPI dependency system.
    """
    hardship_service = get_hardship_service()
    from underwriting_validation.infrastructure.contact_repository import ContactRepository
    repository = ContactRepository(session)
    return ContactService(hardship_service, repository)


async def get_contact_validation_uc(
    session: AsyncSession = Depends(get_db_session),   # ← one session per request
) -> ContactService:
    """
    Dependency injection function for ContactService with proper session management.
    
    This follows the clean dependency injection pattern where:
    - One session per request (injected by FastAPI)
    - Repository holds the session
    - Service uses the repository
    - All database operations use the same session
    """
    hardship_service = get_hardship_service()
    budget_service = get_budget_service()
    from underwriting_validation.infrastructure.contact_repository import ContactRepository
    
    repo = ContactRepository(session)
    return ContactService(hardship_service, repo)


async def get_combined_validation_uc(
    session: AsyncSession = Depends(get_db_session),   # ← one session per request
) -> CombinedValidationService:
    """
    Dependency injection function for CombinedValidationService with proper session management.
    
    This follows the clean dependency injection pattern where:
    - One session per request (injected by FastAPI)
    - Repository holds the session
    - Service uses the repository
    - All database operations use the same session
    """
    hardship_service = get_hardship_service()
    budget_service = get_budget_service()
    from underwriting_validation.infrastructure.contact_repository import ContactRepository
    
    repo = ContactRepository(session)
    return CombinedValidationService(hardship_service, budget_service, repo)







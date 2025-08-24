"""
Contact Repository for database operations.

This repository orchestrates data access by delegating to specialized repositories.
It provides a unified interface for contact-related operations while maintaining
separation of concerns.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from underwriting_validation.infrastructure.base_contact_repository import BaseContactRepository
from underwriting_validation.infrastructure.budget_repository import BudgetRepository
from underwriting_validation.infrastructure.hardship_repository import HardshipRepository
from underwriting_validation.infrastructure.address_repository import AddressRepository
from underwriting_validation.infrastructure.eligibility_repository import EligibilityRepository
from underwriting_validation.infrastructure.contract_repository import ContractRepository
from underwriting_validation.infrastructure.duplication_repository import DuplicationRepository
from underwriting_validation.infrastructure.draft_repository import DraftRepository
from underwriting_validation.infrastructure.credit_score_repository import CreditScoreRepository

logger = logging.getLogger(__name__)

class ContactRepository:
    """Orchestrating repository for contact-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Initialize specialized repositories
        self.base_repo = BaseContactRepository(session)
        self.budget_repo = BudgetRepository(session)
        self.hardship_repo = HardshipRepository(session)
        self.address_repo = AddressRepository(session)
        self.eligibility_repo = EligibilityRepository(session)
        self.contract_repo = ContractRepository(session)
        self.duplication_repo = DuplicationRepository(session)
        self.draft_repo = DraftRepository(session)
        self.credit_score_repo = CreditScoreRepository(session)
        
        logger.info("ContactRepository initialized with specialized repositories")
    
    # Core contact operations
    async def fetch_contact(self, contact_id: int) -> Optional[Any]:
        """Fetch a single contact by ID with soft-delete filtering."""
        return await self.base_repo.fetch_contact(contact_id)
    
    async def contact_exists(self, contact_id: int) -> bool:
        """Check if a contact exists and is not deleted."""
        return await self.base_repo.contact_exists(contact_id)
    
    # Budget operations
    async def fetch_contact_with_budget_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with budget data using a single query."""
        return await self.budget_repo.fetch_contact_with_budget_data(contact_id)
    
    # Hardship operations
    async def fetch_contact_with_hardship_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with hardship data using a single query."""
        return await self.hardship_repo.fetch_contact_with_hardship_data(contact_id)
    
    # Address operations
    async def fetch_contact_with_address_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with address validation data using the provided SQL query."""
        return await self.address_repo.fetch_contact_with_address_data(contact_id)
    
    # Credit Score operations
    async def fetch_contact_with_credit_score_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with credit score validation data using the provided SQL query."""
        return await self.credit_score_repo.fetch_contact_with_credit_score_data(contact_id)
    
    # Eligibility operations
    async def check_contact_eligibility(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Check if a contact is eligible for validation process."""
        return await self.eligibility_repo.check_contact_eligibility(contact_id)
    
    # Contract operations
    async def fetch_contact_with_contract_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with contract validation data using multiple queries."""
        return await self.contract_repo.fetch_contact_with_contract_data(contact_id)
    
    # Duplication operations
    async def fetch_contact_with_duplication_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with duplication validation data."""
        return await self.duplication_repo.check_contact_duplication(contact_id)
    
    # Draft operations
    async def fetch_contact_with_draft_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with draft validation data."""
        return await self.draft_repo.fetch_contact_with_draft_data(contact_id)
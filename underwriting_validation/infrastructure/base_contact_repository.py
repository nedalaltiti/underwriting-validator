"""
Base Contact Repository for core contact operations.

This repository provides basic contact data access methods.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, null, bindparam
from underwriting_validation.db.models import Contact

logger = logging.getLogger(__name__)

class BaseContactRepository:
    """Base repository for core contact operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contact(self, contact_id: int) -> Optional[Contact]:
        """Fetch a single contact by ID with soft-delete filtering."""
        stmt = (
            select(Contact)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter: not deleted (del IS NULL OR del != true)
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    )
                )
            )
        )
        
        result = await self.session.execute(stmt, {"contact_id": contact_id})
        return result.scalar_one_or_none()
    
    async def contact_exists(self, contact_id: int) -> bool:
        """Check if a contact exists and is not deleted."""
        contact = await self.fetch_contact(contact_id)
        return contact is not None

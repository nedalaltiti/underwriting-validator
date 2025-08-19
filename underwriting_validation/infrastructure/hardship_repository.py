"""
Hardship Repository for hardship-related data operations.

This repository handles hardship data queries.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, bindparam
from underwriting_validation.db.models import Contact, ContactUserField
from underwriting_validation.config.settings import settings

logger = logging.getLogger(__name__)

class HardshipRepository:
    """Repository for hardship-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Get field IDs from settings
        self.financial_hardship_id = settings.hardship_fields.financial_hardship_id
        self.hardship_description_id = settings.hardship_fields.hardship_description_id
    
    async def fetch_contact_with_hardship_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with hardship data using a single query."""
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.del_,
                Contact.iscoapp,
                Contact.c_type,
                Contact.leadstatus,
                func.max(case(
                    (ContactUserField.custom_id == self.financial_hardship_id, 
                     ContactUserField.f_string)
                )).label('financial_hardship'),
                func.max(case(
                    (ContactUserField.custom_id == self.hardship_description_id, 
                     ContactUserField.f_string)
                )).label('hardship_description')
            )
            .outerjoin(ContactUserField, Contact.id == ContactUserField.contact_id)
            .where(Contact.id == contact_id)
            .group_by(
                Contact.id,
                Contact.acctid,
                Contact.del_,
                Contact.iscoapp,
                Contact.c_type,
                Contact.leadstatus
            )
        )
        
        result = await self.session.execute(stmt)
        row = result.fetchone()
        
        if row:
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "del": row.del_,
                "iscoapp": row.iscoapp,
                "c_type": row.c_type,
                "leadstatus": row.leadstatus,
                "financial_hardship": row.financial_hardship,
                "hardship_description": row.hardship_description,
            }
        return None

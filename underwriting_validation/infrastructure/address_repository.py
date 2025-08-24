"""
Address Repository for address validation data operations.

This repository handles address validation queries.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, case, bindparam, and_, null
from underwriting_validation.db.models import Contact, Company
from underwriting_validation.config.settings import settings

logger = logging.getLogger(__name__)

class AddressRepository:
    """Repository for address validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Get address-specific field values from settings
        self.address_company_type = settings.address_fields.company_type
    
    async def fetch_contact_with_address_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with address validation data using the provided SQL query."""
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.state,
                Company.name.label('assigned_company'),
                case(
                    # Clarity Debt Resolution, Inc. (company_ids: 26267, 87758)
                    (and_(
                        Contact.company_id.in_([26267, 87758]),
                        Contact.state.in_(['AL','AK','AZ','AR','CA','CO','DC','FL','ID','IN','KY','MD',
                                         'MA','MI','MN','MS','MO','MT','NE','NM','NY','NC','OH','OK',
                                         'SD','TN','TX','UT'])
                    ), 'Match'),
                    # Concordia Legal Advisors, PLLC (company_ids: 83850, 89302, 67264)
                    (and_(
                        Contact.company_id.in_([83850, 89302, 67264]),
                        Contact.state.in_(['GA','IL','IA','LA','NV','NJ','PA','PR','VA','WI','WY'])
                    ), 'Match'),
                    # Missing company name
                    (Company.name.is_(null()), 'Missing Value'),
                    # Default case
                    else_='Mismatch'
                ).label('state_check')
            )
            .select_from(Contact)
            .outerjoin(Company, and_(
                Company.id == Contact.company_id,
                Company.company_type.in_([2, 7])
            ))
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                )
            )
        )
        
        result = await self.session.execute(stmt, {"contact_id": contact_id})
        row = result.fetchone()
        
        if row:
            # Determine the result based on state_check only (since we only have state_check now)
            address_validation_result = self._determine_address_result_simple(row.state_check)
            
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "state": row.state,
                "assigned_company": row.assigned_company,
                "state_check": row.state_check,
                "address_validation_result": address_validation_result,
            }
        return None
    
    def _determine_address_result_simple(self, state_check: str) -> str:
        """Determine the address validation result based on state check only."""
        if state_check == 'Match':
            return 'pass'
        elif state_check == 'Mismatch':
            return 'no_pass'
        elif state_check == 'Missing Value':
            return 'no_data'
        else:
            return 'unknown'

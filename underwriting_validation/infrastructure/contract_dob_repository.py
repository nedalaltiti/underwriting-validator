"""
Contract DOB Repository for DOB validation data operations.

This repository handles DOB validation queries for contract validation.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, bindparam, and_, or_, null, String
from underwriting_validation.db.models import Contact, CreditReport, Applicant
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContractDOBRepository:
    """Repository for contract DOB validation database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def fetch_contract_dob_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch DOB data for contract validation."""
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.dob.label('forth_dob'),
                Applicant.date_of_birth.label('contract_dob')
            )
            .select_from(Contact)
            .outerjoin(CreditReport, func.regexp_replace(CreditReport.filename, '^.*/([0-9]+)-.*$', '\\1') == func.cast(Contact.id, String))
            .outerjoin(Applicant, Applicant.credit_report_id == CreditReport.id)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    )
                )
            )
        )
        
        result = await self.session.execute(stmt, {"contact_id": contact_id})
        row = result.fetchone()
        
        if row and (row.forth_dob or row.contract_dob):
            # Calculate DOB check
            dob_check = "Missing Value"
            if row.forth_dob and row.contract_dob:
                if row.forth_dob == row.contract_dob:
                    dob_check = "Match"
                else:
                    dob_check = "Mismatch"
            
            # Calculate age check
            age_plus_18_check = "Unknown Age"
            if row.forth_dob:
                # Calculate age using SQL function
                age_stmt = select(
                    func.date_part('year', func.age(row.forth_dob)).label('age')
                )
                age_result = await self.session.execute(age_stmt)
                age_row = age_result.fetchone()
                if age_row and age_row.age >= 18:
                    age_plus_18_check = "Yes"
                else:
                    age_plus_18_check = "No"
            
            return {
                "contact_id": contact_id,
                "acctid": row.acctid,
                "forth_dob": row.forth_dob,
                "contract_dob": row.contract_dob,
                "dob_check": dob_check,
                "age_plus_18_check": age_plus_18_check
            }
        return None

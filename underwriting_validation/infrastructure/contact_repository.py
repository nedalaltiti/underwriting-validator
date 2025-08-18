"""
Contact Repository for database operations.

This repository holds a single database session and provides data access methods
for contact-related operations. It ensures consistent transactions and efficient
connection pool usage.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, bindparam, and_, or_, null, Integer
from underwriting_validation.db.models import Contact, ContactUserField, BudgetData, BudgetFields, Company, ContactCategory, ContactLeadStatus, ContactFile, PaymentGatewayBankInfo, BankAccount, LegalPlanAgreement, EnrollmentPlan, EnrollmentDefaults2, PaymentScheduleData, PaymentGatewayDepositSchedule, PaymentGatewayAgreement
from underwriting_validation.config.settings import settings
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class ContactRepository:
    """Repository for contact-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Get field IDs from settings
        self.financial_hardship_id = settings.hardship_fields.financial_hardship_id
        self.hardship_description_id = settings.hardship_fields.hardship_description_id
        
        # Get budget field values from settings
        self.budget_acctid = settings.budget_fields.acctid
        self.budget_c_type = settings.budget_fields.c_type
        self.budget_iscoapp = settings.budget_fields.iscoapp
        self.budget_leadstatus = settings.budget_fields.leadstatus
        
        # Get address field values from settings
        self.address_acctid = settings.address_fields.acctid
        self.address_c_type = settings.address_fields.c_type
        self.address_iscoapp = settings.address_fields.iscoapp
        self.address_leadstatus = settings.address_fields.leadstatus
        self.address_company_type = settings.address_fields.company_type
    
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
    
    async def fetch_contact_with_budget_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with budget data using a single query."""
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.del_,
                Contact.iscoapp,
                Contact.c_type,
                Contact.leadstatus,
                func.sum(
                    case(
                        (BudgetFields.field_type == 'I', BudgetData.field_val),
                        else_=0
                    )
                ).label('total_net_income'),
                func.sum(
                    case(
                        (BudgetFields.field_type == 'E', BudgetData.field_val),
                        else_=0
                    )
                ).label('total_expenses')
            )
            .select_from(Contact)
            .outerjoin(BudgetData, Contact.id == BudgetData.contact_id)
            .outerjoin(BudgetFields, BudgetData.field_id == BudgetFields.id)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    ),
                    # Additional filters from environment variables
                    Contact.acctid == self.budget_acctid,
                    Contact.c_type == self.budget_c_type,
                    Contact.iscoapp == self.budget_iscoapp,
                    Contact.leadstatus == self.budget_leadstatus
                )
            )
            .group_by(
                Contact.id, 
                Contact.acctid, 
                Contact.del_, 
                Contact.iscoapp, 
                Contact.c_type, 
                Contact.leadstatus
            )
        )
        
        result = await self.session.execute(stmt, {"contact_id": contact_id})
        row = result.fetchone()
        
        if row:
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "del_flag": row.del_,
                "iscoapp": row.iscoapp,
                "c_type": row.c_type,
                "leadstatus": row.leadstatus,
                "total_net_income": float(row.total_net_income or 0),
                "total_expenses": float(row.total_expenses or 0),
            }
        return None
    
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
                    # Address validation filters from environment variables
                    Contact.acctid == self.address_acctid,
                    Contact.c_type == self.address_c_type,
                    Contact.del_ == False,  # Exclude deleted clients
                    Contact.iscoapp == self.address_iscoapp,  # Exclude co-app
                    Contact.leadstatus == self.address_leadstatus  # Include just leads with Submitted status
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
    
    async def check_contact_eligibility(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Check if a contact is eligible for validation process."""
        masked_id = mask_contact_id(contact_id)
        logger.debug(f"Executing eligibility check query for contact {masked_id}")
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.email,
                Contact.phone3,
                Contact.del_,
                Contact.iscoapp,
                func.coalesce(ContactCategory.title, 'Unknown').label('contact_category'),
                func.coalesce(ContactLeadStatus.title, 'Unknown').label('contact_lead_status')
            )
            .select_from(Contact)
            .outerjoin(ContactCategory, ContactCategory.id == Contact.c_type)
            .outerjoin(ContactLeadStatus, ContactLeadStatus.id == Contact.leadstatus)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    Contact.acctid != 5783,  # Exclude specific account ID
                    ContactCategory.title == 'Underwriting',  # Only underwriting stage
                    Contact.del_ == False,  # Exclude deleted clients
                    Contact.iscoapp == 0,  # Exclude co-app
                    ContactLeadStatus.title == 'Submitted'  # Only submitted status
                )
            )
        )
        
        result = await self.session.execute(stmt, {"contact_id": contact_id})
        row = result.fetchone()
        
        if row:
            logger.debug(f"Contact {masked_id} eligibility check passed: category={row.contact_category}, status={row.contact_lead_status}")
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "email": row.email,
                "phone3": row.phone3,
                "del_flag": row.del_,
                "iscoapp": row.iscoapp,
                "contact_category": row.contact_category,
                "contact_lead_status": row.contact_lead_status,
                "eligible": True
            }
        logger.debug(f"Contact {masked_id} eligibility check failed: no matching records found")
        return None
    
    async def _fetch_contract_bank_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch bank data for contract validation."""
        # First, get contract bank data
        contract_bank_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentGatewayBankInfo.account_number,
                PaymentGatewayBankInfo.routing_number,
                PaymentGatewayBankInfo.bank_name,
                PaymentGatewayBankInfo.account_type,
                PaymentGatewayBankInfo.address
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(PaymentGatewayBankInfo, PaymentGatewayBankInfo.file_id == ContactFile.id)
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
        
        # Get Forth bank data
        forth_bank_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                BankAccount.account_num,
                BankAccount.routing_num,
                BankAccount.bank_name,
                BankAccount.account_type,
                BankAccount.bank_address
            )
            .select_from(Contact)
            .outerjoin(BankAccount, BankAccount.contact_id == Contact.id)
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
        
        # Execute both queries
        contract_result = await self.session.execute(contract_bank_stmt, {"contact_id": contact_id})
        forth_result = await self.session.execute(forth_bank_stmt, {"contact_id": contact_id})
        
        contract_row = contract_result.fetchone()
        forth_row = forth_result.fetchone()
        
        # Check if we have any bank data
        has_contract_bank_data = contract_row and any([
            contract_row.account_number,
            contract_row.routing_number,
            contract_row.bank_name,
            contract_row.account_type,
            contract_row.address
        ])
        
        has_forth_bank_data = forth_row and any([
            forth_row.account_num,
            forth_row.routing_num,
            forth_row.bank_name,
            forth_row.account_type,
            forth_row.bank_address
        ])
        
        if has_contract_bank_data or has_forth_bank_data:
            # Normalize account type for Forth data
            forth_account_type = None
            if forth_row and forth_row.account_type:
                if forth_row.account_type == '1':
                    forth_account_type = 'checking'
                elif forth_row.account_type == '2':
                    forth_account_type = 'savings'
                else:
                    forth_account_type = forth_row.account_type
            
            return {
                "contact_id": contact_id,
                "acctid": (contract_row or forth_row).acctid if (contract_row or forth_row) else None,
                # Contract bank data
                "contract_account_number": contract_row.account_number if contract_row else None,
                "contract_routing_number": contract_row.routing_number if contract_row else None,
                "contract_bank_name": contract_row.bank_name if contract_row else None,
                "contract_account_type": contract_row.account_type if contract_row else None,
                "contract_address": contract_row.address if contract_row else None,
                # Forth bank data
                "forth_account_number": forth_row.account_num if forth_row else None,
                "forth_routing_number": forth_row.routing_num if forth_row else None,
                "forth_bank_name": forth_row.bank_name if forth_row else None,
                "forth_account_type": forth_account_type,
                "forth_address": forth_row.bank_address if forth_row else None,
            }
        return None

    async def fetch_contact_with_contract_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch contact with contract validation data using multiple queries."""
        masked_id = mask_contact_id(contact_id)
        logger.debug(f"Fetching contract data for contact {masked_id}")
        
        # Fetch IP address data
        ip_data = await self._fetch_contract_ip_data(contact_id)
        
        # Fetch email data
        email_data = await self._fetch_contract_email_data(contact_id)
        
        # Fetch signature data
        signature_data = await self._fetch_contract_signature_data(contact_id)
        
        # Fetch bank data
        bank_data = await self._fetch_contract_bank_data(contact_id)
        
        # Fetch VLP data
        vlp_data = await self._fetch_contract_vlp_data(contact_id)
        
        # Fetch gateway data
        gateway_data = await self._fetch_contract_gateway_data(contact_id)
        
        # Combine all data
        if ip_data or email_data or signature_data or bank_data or vlp_data or gateway_data:
            combined_data = {
                "contact_id": contact_id,
                "acctid": (ip_data or email_data or signature_data or bank_data).get('acctid') if (ip_data or email_data or signature_data or bank_data) else None,
                "sender_ip_address": ip_data.get('sender_ip_address') if ip_data else None,
                "signer_ip_address": ip_data.get('signer_ip_address') if ip_data else None,
                "forth_email": email_data.get('forth_email') if email_data else None,
                "contract_email": email_data.get('contract_email') if email_data else None,
                "client_signature": signature_data.get('client_signature') if signature_data else None,
                "client_signature_date": signature_data.get('client_signature_date') if signature_data else None,
                "coclient_signature": signature_data.get('coclient_signature') if signature_data else None,
                "coclient_signature_date": signature_data.get('coclient_signature_date') if signature_data else None,
                "contract_account_number": bank_data.get('contract_account_number') if bank_data else None,
                "forth_account_number": bank_data.get('forth_account_number') if bank_data else None,
                "contract_routing_number": bank_data.get('contract_routing_number') if bank_data else None,
                "forth_routing_number": bank_data.get('forth_routing_number') if bank_data else None,
                "contract_bank_name": bank_data.get('contract_bank_name') if bank_data else None,
                "forth_bank_name": bank_data.get('forth_bank_name') if bank_data else None,
                "contract_account_type": bank_data.get('contract_account_type') if bank_data else None,
                "forth_account_type": bank_data.get('forth_account_type') if bank_data else None,
                "contract_address": bank_data.get('contract_address') if bank_data else None,
                "forth_address": bank_data.get('forth_address') if bank_data else None,
                # VLP data
                "legal_plan_provider": vlp_data.get('legal_plan_provider') if vlp_data else None,
                "client_signature": vlp_data.get('client_signature') if vlp_data else None,
                "signature_date": vlp_data.get('signature_date') if vlp_data else None,
                "contract_name": vlp_data.get('contract_name') if vlp_data else None,
                "forth_name": vlp_data.get('forth_name') if vlp_data else None,
                "contract_ssn": vlp_data.get('contract_ssn') if vlp_data else None,
                "forth_ssn": vlp_data.get('forth_ssn') if vlp_data else None,
                "contract_dob": vlp_data.get('contract_dob') if vlp_data else None,
                "forth_dob": vlp_data.get('forth_dob') if vlp_data else None,
                "legal_setup_fee_snapshot": vlp_data.get('legal_setup_fee_snapshot') if vlp_data else None,
                "legal_monthly_fee_snapshot": vlp_data.get('legal_monthly_fee_snapshot') if vlp_data else None,
                "legal_setup_fee_enrollment": vlp_data.get('legal_setup_fee_enrollment') if vlp_data else None,
                "legal_monthly_fee_enrollment": vlp_data.get('legal_monthly_fee_enrollment') if vlp_data else None,
                "payment_date": vlp_data.get('payment_date') if vlp_data else None,
                "plan_name": vlp_data.get('plan_name') if vlp_data else None,
                # Gateway data
                "gateway_client_signature": gateway_data.get('gateway_client_signature') if gateway_data else None,
                "contract_payment_count": gateway_data.get('contract_payment_count') if gateway_data else None,
                "forth_payment_count": gateway_data.get('forth_payment_count') if gateway_data else None,
                "count_check": gateway_data.get('count_check') if gateway_data else None,
                "payment_details": gateway_data.get('payment_details') if gateway_data else None,
            }
            
            logger.debug(f"Contract data fetched for contact {masked_id}")
            return combined_data
        
        logger.debug(f"No contract data found for contact {masked_id}")
        return None
    
    async def _fetch_contract_ip_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch IP address data for contract validation."""
        from underwriting_validation.db.models import ClixsignCertificateSender, ClixsignCertificateSigner
        
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                ClixsignCertificateSender.sender_ip_address,
                ClixsignCertificateSigner.signer_ip_address
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(ClixsignCertificateSender, ClixsignCertificateSender.file_id == ContactFile.id)
            .outerjoin(ClixsignCertificateSigner, ClixsignCertificateSigner.file_id == ContactFile.id)
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
        
        if row and (row.sender_ip_address or row.signer_ip_address):
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "sender_ip_address": row.sender_ip_address,
                "signer_ip_address": row.signer_ip_address
            }
        return None
    
    async def _fetch_contract_email_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch email data for contract validation."""
        from underwriting_validation.db.models import FinancialAnalysis
        
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.email.label('forth_email'),
                FinancialAnalysis.applicant_email.label('contract_email')
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(FinancialAnalysis, FinancialAnalysis.file_id == ContactFile.id)
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
        
        if row and (row.forth_email or row.contract_email):
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "forth_email": row.forth_email,
                "contract_email": row.contract_email
            }
        return None
    
    async def _fetch_contract_signature_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch signature data for contract validation."""
        from underwriting_validation.db.models import EngagementTerm
        
        stmt = (
            select(
                Contact.id,
                Contact.acctid,
                EngagementTerm.client_signature,
                EngagementTerm.client_signature_date,
                EngagementTerm.coclient_signature,
                EngagementTerm.coclient_signature_date
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(EngagementTerm, EngagementTerm.file_id == ContactFile.id)
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
        
        if row and (row.client_signature or row.coclient_signature):
            return {
                "contact_id": row.id,
                "acctid": row.acctid,
                "client_signature": row.client_signature,
                "client_signature_date": row.client_signature_date,
                "coclient_signature": row.coclient_signature,
                "coclient_signature_date": row.coclient_signature_date
            }
        return None
    
    async def _fetch_contract_vlp_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch VLP (Voluntary Legal Plan) data for contract validation."""
        # Main VLP agreement data query
        vlp_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                Contact.firstname,
                Contact.lastname,
                Contact.ssn.label('forth_ssn'),
                Contact.dob.label('forth_dob'),
                LegalPlanAgreement.legal_plan_provider,
                LegalPlanAgreement.client_signature,
                LegalPlanAgreement.signature_date,
                LegalPlanAgreement.member_name.label('contract_name'),
                LegalPlanAgreement.member_ssn.label('contract_ssn'),
                LegalPlanAgreement.member_dob.label('contract_dob')
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(LegalPlanAgreement, LegalPlanAgreement.file_id == ContactFile.id)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    ),
                    # Only include records with legal plan provider
                    LegalPlanAgreement.legal_plan_provider.isnot(None)
                )
            )
        )
        
        # Client snapshot fees query
        snapshot_fees_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                func.split_part(EnrollmentPlan.fee2, ',', 4).label('legal_setup_fee_snapshot'),
                func.split_part(EnrollmentPlan.fee3, ',', 4).label('legal_monthly_fee_snapshot')
            )
            .select_from(Contact)
            .outerjoin(EnrollmentPlan, EnrollmentPlan.contact_id == Contact.id)
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
        
        # Enrollment tab fees query
        enrollment_fees_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentScheduleData.payment_date,
                PaymentScheduleData.fee2.label('legal_setup_fee_enrollment'),
                PaymentScheduleData.fee3.label('legal_monthly_fee_enrollment')
            )
            .select_from(Contact)
            .outerjoin(PaymentScheduleData, PaymentScheduleData.contact_id == Contact.id)
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
        
        # Enrollment plan name query
        plan_name_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                EnrollmentDefaults2.title.label('plan_name')
            )
            .select_from(Contact)
            .outerjoin(EnrollmentPlan, EnrollmentPlan.contact_id == Contact.id)
            .outerjoin(EnrollmentDefaults2, EnrollmentDefaults2.id == EnrollmentPlan.plan_id)
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
        
        # Execute all queries
        vlp_result = await self.session.execute(vlp_stmt, {"contact_id": contact_id})
        snapshot_fees_result = await self.session.execute(snapshot_fees_stmt, {"contact_id": contact_id})
        enrollment_fees_result = await self.session.execute(enrollment_fees_stmt, {"contact_id": contact_id})
        plan_name_result = await self.session.execute(plan_name_stmt, {"contact_id": contact_id})
        
        vlp_row = vlp_result.fetchone()
        snapshot_fees_row = snapshot_fees_result.fetchone()
        enrollment_fees_row = enrollment_fees_result.fetchone()
        plan_name_row = plan_name_result.fetchone()
        
        # Check if we have any VLP data
        has_vlp_data = vlp_row and vlp_row.legal_plan_provider
        has_fees_data = (snapshot_fees_row and (snapshot_fees_row.legal_setup_fee_snapshot or snapshot_fees_row.legal_monthly_fee_snapshot)) or \
                       (enrollment_fees_row and (enrollment_fees_row.legal_setup_fee_enrollment or enrollment_fees_row.legal_monthly_fee_enrollment))
        has_plan_data = plan_name_row and plan_name_row.plan_name
        
        if has_vlp_data or has_fees_data or has_plan_data:
            # Build forth name from firstname and lastname
            forth_name = None
            if vlp_row and vlp_row.firstname and vlp_row.lastname:
                forth_name = f"{vlp_row.firstname} {vlp_row.lastname}".strip()
            elif vlp_row and vlp_row.firstname:
                forth_name = vlp_row.firstname
            elif vlp_row and vlp_row.lastname:
                forth_name = vlp_row.lastname
            
            return {
                "contact_id": contact_id,
                "acctid": (vlp_row or snapshot_fees_row or enrollment_fees_row or plan_name_row).acctid if (vlp_row or snapshot_fees_row or enrollment_fees_row or plan_name_row) else None,
                # VLP agreement data
                "legal_plan_provider": vlp_row.legal_plan_provider if vlp_row else None,
                "client_signature": vlp_row.client_signature if vlp_row else None,
                "signature_date": vlp_row.signature_date if vlp_row else None,
                "contract_name": vlp_row.contract_name if vlp_row else None,
                "forth_name": forth_name,
                "contract_ssn": vlp_row.contract_ssn if vlp_row else None,
                "forth_ssn": vlp_row.forth_ssn if vlp_row else None,
                "contract_dob": vlp_row.contract_dob if vlp_row else None,
                "forth_dob": vlp_row.forth_dob if vlp_row else None,
                # Client snapshot fees
                "legal_setup_fee_snapshot": snapshot_fees_row.legal_setup_fee_snapshot if snapshot_fees_row else None,
                "legal_monthly_fee_snapshot": snapshot_fees_row.legal_monthly_fee_snapshot if snapshot_fees_row else None,
                # Enrollment tab fees
                "legal_setup_fee_enrollment": enrollment_fees_row.legal_setup_fee_enrollment if enrollment_fees_row else None,
                "legal_monthly_fee_enrollment": enrollment_fees_row.legal_monthly_fee_enrollment if enrollment_fees_row else None,
                "payment_date": enrollment_fees_row.payment_date if enrollment_fees_row else None,
                # Enrollment plan name
                "plan_name": plan_name_row.plan_name if plan_name_row else None,
            }
        return None
    
    async def _fetch_contract_gateway_data(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Fetch gateway data for contract validation."""
        # Gateway signature query
        signature_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentGatewayAgreement.client_signature
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(PaymentGatewayAgreement, PaymentGatewayAgreement.file_id == ContactFile.id)
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
        
        # Payment count query
        payment_count_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentGatewayAgreement.file_id,
                func.max(func.cast(PaymentGatewayDepositSchedule.payment_no, Integer)).label('contract_payment_count'),
                func.max(PaymentScheduleData.payment_num).label('forth_payment_count')
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(PaymentGatewayAgreement, PaymentGatewayAgreement.file_id == ContactFile.id)
            .outerjoin(PaymentGatewayDepositSchedule, PaymentGatewayDepositSchedule.file_id == ContactFile.id)
            .outerjoin(PaymentScheduleData, PaymentScheduleData.contact_id == Contact.id)
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    ),
                    # Only include non-deleted payment schedule data
                    PaymentScheduleData._fivetran_deleted == False
                )
            )
            .group_by(Contact.id, Contact.acctid, PaymentGatewayAgreement.file_id)
        )
        
        # Payment amounts and dates query
        payment_details_stmt = (
            select(
                Contact.id,
                Contact.acctid,
                PaymentGatewayAgreement.file_id,
                PaymentScheduleData.payment_num,
                PaymentGatewayDepositSchedule.amount.label('contract_amount'),
                PaymentScheduleData.fee1.label('forth_amount'),
                PaymentGatewayDepositSchedule.process_date.label('contract_date'),
                PaymentScheduleData.payment_date.label('forth_date')
            )
            .select_from(Contact)
            .outerjoin(ContactFile, ContactFile.contact_id == Contact.id)
            .outerjoin(PaymentGatewayAgreement, PaymentGatewayAgreement.file_id == ContactFile.id)
            .outerjoin(PaymentGatewayDepositSchedule, PaymentGatewayDepositSchedule.file_id == ContactFile.id)
            .outerjoin(
                PaymentScheduleData, 
                and_(
                    PaymentScheduleData.contact_id == Contact.id,
                    PaymentScheduleData.payment_num == func.cast(PaymentGatewayDepositSchedule.payment_no, Integer)
                )
            )
            .where(
                and_(
                    Contact.id == bindparam('contact_id'),
                    # Soft-delete filter
                    or_(
                        Contact.del_.is_(null()),
                        Contact.del_ != True
                    ),
                    # Only include non-deleted payment schedule data
                    PaymentScheduleData._fivetran_deleted == False
                )
            )
        )
        
        # Execute all queries
        signature_result = await self.session.execute(signature_stmt, {"contact_id": contact_id})
        payment_count_result = await self.session.execute(payment_count_stmt, {"contact_id": contact_id})
        payment_details_result = await self.session.execute(payment_details_stmt, {"contact_id": contact_id})
        
        signature_row = signature_result.fetchone()
        payment_count_row = payment_count_result.fetchone()
        payment_details_rows = payment_details_result.fetchall()
        
        # Check if we have any gateway data
        has_signature_data = signature_row and signature_row.client_signature
        has_payment_count_data = payment_count_row and (payment_count_row.contract_payment_count or payment_count_row.forth_payment_count)
        has_payment_details_data = len(payment_details_rows) > 0
        
        if has_signature_data or has_payment_count_data or has_payment_details_data:
            # Calculate payment count check
            count_check = "Missing Value"
            if payment_count_row and payment_count_row.contract_payment_count is not None and payment_count_row.forth_payment_count is not None:
                if payment_count_row.contract_payment_count == payment_count_row.forth_payment_count:
                    count_check = "Match"
                else:
                    count_check = "Mismatch"
            
            # Process payment details
            payment_details = []
            for row in payment_details_rows:
                amount_check = "Missing Value"
                if row.contract_amount is not None and row.forth_amount is not None:
                    if row.contract_amount == row.forth_amount:
                        amount_check = "Match"
                    else:
                        amount_check = "Mismatch"
                
                date_check = "Missing Value"
                if row.contract_date is not None and row.forth_date is not None:
                    if row.contract_date == row.forth_date:
                        date_check = "Match"
                    else:
                        date_check = "Mismatch"
                
                payment_details.append({
                    "payment_num": row.payment_num,
                    "contract_amount": row.contract_amount,
                    "forth_amount": row.forth_amount,
                    "amount_check": amount_check,
                    "amount_diff": abs((row.contract_amount or 0) - (row.forth_amount or 0)),
                    "contract_date": row.contract_date,
                    "forth_date": row.forth_date,
                    "date_check": date_check
                })
            
            return {
                "contact_id": contact_id,
                "acctid": (signature_row or payment_count_row).acctid if (signature_row or payment_count_row) else None,
                # Gateway signature data
                "gateway_client_signature": signature_row.client_signature if signature_row else None,
                # Payment count data
                "contract_payment_count": payment_count_row.contract_payment_count if payment_count_row else None,
                "forth_payment_count": payment_count_row.forth_payment_count if payment_count_row else None,
                "count_check": count_check,
                # Payment details data
                "payment_details": payment_details
            }
        return None
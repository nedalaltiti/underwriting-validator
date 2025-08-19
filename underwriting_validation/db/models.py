from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, SmallInteger, String,
    Text, TIMESTAMP, ForeignKey, MetaData, Boolean, Float, Numeric, Date
)
from sqlalchemy.orm import registry, relationship

# Create a separate metadata for the public schema
public_metadata = MetaData(schema="public")
public_mapper = registry(metadata=public_metadata)


@public_mapper.mapped
class Contact:
    __tablename__ = "contacts"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    acctid = Column(Numeric, nullable=True)
    email = Column(Text, nullable=True)
    phone3 = Column(Text, nullable=True)
    del_ = Column("del", Boolean, nullable=True)  # Using del_ to avoid Python keyword conflict, maps to "del" column - boolean for soft delete
    iscoapp = Column(Numeric, nullable=True)
    c_type = Column(Numeric, nullable=True)
    leadstatus = Column(Numeric, nullable=True)
    state = Column(Text, nullable=True)  # State field for address validation; Text type for unlimited length
    company_id = Column(Numeric, nullable=True)  # Company ID for address validation
    firstname = Column(Text, nullable=True)  # First name for VLP validation
    lastname = Column(Text, nullable=True)  # Last name for VLP validation
    ssn = Column(Text, nullable=True)  # SSN for VLP validation
    dob = Column(Date, nullable=True)  # Date of birth for VLP validation

@public_mapper.mapped
class ContactCategory:
    __tablename__ = "contacts_categories"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=True)

@public_mapper.mapped
class ContactLeadStatus:
    __tablename__ = "contacts_lead_status"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=True)

@public_mapper.mapped
class ContactUserField:
    __tablename__ = "contacts_userfields"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    contact_id = Column(Numeric, ForeignKey("public.contacts.id"), nullable=False)
    custom_id = Column(Numeric, nullable=False)
    f_string = Column(Text, nullable=True)
    f_text = Column(Text, nullable=True)
    f_int = Column(Numeric, nullable=True)
    f_float = Column(BigInteger, nullable=True)  # Using BigInteger for compatibility
    f_date = Column(Date, nullable=True)
    f_datetime = Column(TIMESTAMP, nullable=True)
    f_bool = Column(Boolean, nullable=True)

@public_mapper.mapped
class BudgetData:
    __tablename__ = "budget_data"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    contact_id = Column(Numeric, ForeignKey("public.contacts.id"), nullable=False)
    field_id = Column(Numeric, ForeignKey("public.budget_fields.id"), nullable=False)
    field_val = Column(Numeric, nullable=True)

@public_mapper.mapped
class BudgetFields:
    __tablename__ = "budget_fields"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    field_type = Column(Text, nullable=False)  # 'I' for Income, 'E' for Expense
    field_name = Column(Text, nullable=True)
    field_description = Column(Text, nullable=True)

# New models for address validation
@public_mapper.mapped
class Company:
    __tablename__ = "companies"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)
    company_type = Column(Numeric, nullable=True)

@public_mapper.mapped
class ContactFile:
    __tablename__ = "contacts_files"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    contact_id = Column(Numeric, ForeignKey("public.contacts.id"), nullable=False)

# Underwriting schema models
@public_mapper.mapped
class PaymentGatewayAgreement:
    __tablename__ = "payment_gateway_agreement"
    __table_args__ = {"schema": "underwriting"}

    file_id = Column(Numeric,primary_key=True, autoincrement=True)
    client_state = Column(String(255), nullable=True)
    client_signature = Column(String(255), nullable=True)
    client_ssn = Column(String(255), nullable=True)

@public_mapper.mapped
class EngagementTerm:
    __tablename__ = "engagement_term"
    __table_args__ = {"schema": "underwriting"}

    file_id = Column(Numeric, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=True)
    client_signature = Column(String(255), nullable=True)
    client_signature_date = Column(Date, nullable=True)
    coclient_signature = Column(String(255), nullable=True)
    coclient_signature_date = Column(Date, nullable=True)

@public_mapper.mapped
class ClixsignCertificateSender:
    __tablename__ = "clixsign_certificate_sender"
    __table_args__ = {"schema": "underwriting"}

    file_id = Column(Numeric, primary_key=True, autoincrement=True)
    sender_ip_address = Column(String(32), nullable=True) 

@public_mapper.mapped
class ClixsignCertificateSigner:
    __tablename__ = "clixsign_certificate_signer"
    __table_args__ = {"schema": "underwriting"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    file_id = Column(Numeric, nullable=True)
    signer_ip_address = Column(String(32), nullable=True)  

@public_mapper.mapped
class FinancialAnalysis:
    __tablename__ = "financial_analysis"
    __table_args__ = {"schema": "underwriting"}

    file_id = Column(BigInteger, primary_key=True, autoincrement=True)
    applicant_email = Column(String(255), nullable=True)

@public_mapper.mapped
class PaymentGatewayBankInfo:
    __tablename__ = "payment_gateway_bank_info"
    __table_args__ = {"schema": "underwriting"}

    file_id = Column(Numeric, primary_key=True, autoincrement=True)
    account_number = Column(String(255), nullable=True)
    routing_number = Column(String(255), nullable=True)
    bank_name = Column(String(255), nullable=True)
    account_type = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)

@public_mapper.mapped
class BankAccount:
    __tablename__ = "bank_accounts"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    contact_id = Column(Numeric, ForeignKey("public.contacts.id"), nullable=False)
    account_num = Column(Text, nullable=True)
    routing_num = Column(Text, nullable=True)
    bank_name = Column(Text, nullable=True)
    account_type = Column(Text, nullable=True)
    bank_address = Column(Text, nullable=True)

# VLP (Voluntary Legal Plan) models
@public_mapper.mapped
class LegalPlanAgreement:
    __tablename__ = "legal_plan_agreement"
    __table_args__ = {"schema": "underwriting"}

    file_id = Column(Numeric, primary_key=True, autoincrement=True)
    legal_plan_provider = Column(String(255), nullable=True)
    client_signature = Column(String(255), nullable=True)
    signature_date = Column(Date, nullable=True)
    member_name = Column(String(255), nullable=True)
    member_ssn = Column(String(255), nullable=True)
    member_dob = Column(Date, nullable=True)

@public_mapper.mapped
class EnrollmentPlan:
    __tablename__ = "enrollment_plan"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    contact_id = Column(Numeric, ForeignKey("public.contacts.id"), nullable=False)
    plan_id = Column(Numeric, nullable=True)
    fee2 = Column(Text, nullable=True)  # Legal setup fee
    fee3 = Column(Text, nullable=True)  # Legal monthly fee

@public_mapper.mapped
class EnrollmentDefaults2:
    __tablename__ = "enrollment_defaults2"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=True)

@public_mapper.mapped
class PaymentScheduleData:
    __tablename__ = "payment_schedule_data"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    contact_id = Column(Numeric, ForeignKey("public.contacts.id"), nullable=False)
    payment_date = Column(Date, nullable=True)
    fee2 = Column(Numeric, nullable=True)  # Legal setup fee
    fee3 = Column(Numeric, nullable=True)  # Legal monthly fee
    fee1 = Column(Numeric, nullable=True)  # Payment amount
    payment_num = Column(Numeric, nullable=True)  # Payment number
    _fivetran_deleted = Column(Boolean, nullable=True)  # Soft delete flag

# Gateway models
@public_mapper.mapped
class PaymentGatewayDepositSchedule:
    __tablename__ = "payment_gateway_deposit_schedule"
    __table_args__ = {"schema": "underwriting"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    file_id = Column(Numeric, nullable=True)
    payment_no = Column(String(255), nullable=True)
    amount = Column(Numeric, nullable=True)
    process_date = Column(Date, nullable=True)

# Additional contract validation models
@public_mapper.mapped
class PowerOfAttorney:
    __tablename__ = "power_of_attorney"
    __table_args__ = {"schema": "underwriting"}

    file_id = Column(Numeric, primary_key=True, autoincrement=True)
    client_ssn = Column(String(255), nullable=True)

@public_mapper.mapped
class DebtSchedule:
    __tablename__ = "debt_schedule"
    __table_args__ = {"schema": "underwriting"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_id = Column(BigInteger, nullable=True)

@public_mapper.mapped
class Debt:
    __tablename__ = "debts"
    __table_args__ = {"schema": "public"}

    id = Column(Numeric, primary_key=True, autoincrement=True)
    contact_id = Column(Numeric, ForeignKey("public.contacts.id"), nullable=False)
    enrolled = Column(Numeric, nullable=True)

# Credit report models
@public_mapper.mapped
class CreditReport:
    __tablename__ = "credit_reports"
    __table_args__ = {"schema": "creditreport_parsing"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=True)

@public_mapper.mapped
class Applicant:
    __tablename__ = "applicants"
    __table_args__ = {"schema": "creditreport_parsing"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    credit_report_id = Column(BigInteger, ForeignKey("creditreport_parsing.credit_reports.id"), nullable=False)
    ssn = Column(String(255), nullable=True)
    date_of_birth = Column(Date, nullable=True)
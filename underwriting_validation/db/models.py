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

@public_mapper.mapped
class EngagementTerm:
    __tablename__ = "engagement_term"
    __table_args__ = {"schema": "underwriting"}

    file_id = Column(Numeric, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=True)
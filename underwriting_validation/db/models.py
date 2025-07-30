from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, SmallInteger, String,
    Text, TIMESTAMP, ForeignKey, MetaData, Boolean, Float
)
from sqlalchemy.orm import registry, relationship

# Create a separate metadata for the public schema
public_metadata = MetaData(schema="public")
public_mapper = registry(metadata=public_metadata)


@public_mapper.mapped
class Contact:
    __tablename__ = "contacts"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    acctid = Column(String(255), nullable=True)
    del_ = Column("del", Boolean, nullable=True)  # Using del_ to avoid Python keyword conflict, maps to "del" column - boolean for soft delete
    iscoapp = Column(String(1), nullable=True)
    c_type = Column(String(50), nullable=True)
    leadstatus = Column(String(50), nullable=True)

@public_mapper.mapped
class ContactUserField:
    __tablename__ = "contacts_userfields"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contact_id = Column(BigInteger, ForeignKey("public.contacts.id"), nullable=False)
    custom_id = Column(BigInteger, nullable=False)
    f_string = Column(Text, nullable=True)
    f_text = Column(Text, nullable=True)
    f_int = Column(BigInteger, nullable=True)
    f_float = Column(BigInteger, nullable=True)  # Using BigInteger for compatibility
    f_date = Column(TIMESTAMP, nullable=True)
    f_datetime = Column(TIMESTAMP, nullable=True)
    f_bool = Column(String(1), nullable=True)

@public_mapper.mapped
class BudgetData:
    __tablename__ = "budget_data"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contact_id = Column(BigInteger, ForeignKey("public.contacts.id"), nullable=False)
    field_id = Column(BigInteger, ForeignKey("public.budget_fields.id"), nullable=False)
    field_val = Column(Float, nullable=True)

@public_mapper.mapped
class BudgetFields:
    __tablename__ = "budget_fields"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    field_type = Column(String(1), nullable=False)  # 'I' for Income, 'E' for Expense
    field_name = Column(String(255), nullable=True)
    field_description = Column(Text, nullable=True)
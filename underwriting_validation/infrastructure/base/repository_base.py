"""
Base class for repository implementations.

This module provides base functionality for all repository classes,
eliminating DRY violations in database access patterns.
"""

import logging
from typing import Any, Dict, Optional, List
from sqlalchemy import select, and_, or_, null, bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from abc import ABC, abstractmethod

from underwriting_validation.utils.pii_filter import mask_contact_id


class RepositoryBase(ABC):
    """
    Base class for all repository implementations.
    
    Provides common database access patterns and eliminates DRY violations
    across repository classes.
    """
    
    def __init__(self, session: AsyncSession, repository_name: str):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
            repository_name: Name of the repository for logging
        """
        self.session = session
        self.repository_name = repository_name
        self.logger = logging.getLogger(f"{__name__}.{repository_name}")
        self.logger.info(f"{repository_name} initialized")
    
    def log_query_start(self, contact_id: int, operation: str):
        """
        Log query start with PII-safe contact ID.
        
        Args:
            contact_id: Contact ID being queried
            operation: Description of the operation
        """
        masked_id = mask_contact_id(contact_id)
        self.logger.debug(f"Executing {operation} for contact {masked_id}")
    
    def log_query_result(self, contact_id: int, operation: str, found_data: bool):
        """
        Log query result with PII-safe contact ID.
        
        Args:
            contact_id: Contact ID that was queried
            operation: Description of the operation
            found_data: Whether data was found
        """
        masked_id = mask_contact_id(contact_id)
        status = "found" if found_data else "not found"
        self.logger.debug(f"{operation} for contact {masked_id}: data {status}")
    
    def create_base_contact_filter(self, contact_id: int):
        """
        Create base filter for contact queries with soft-delete handling.
        
        Args:
            contact_id: Contact ID to filter by
            
        Returns:
            SQLAlchemy filter condition
        """
        from underwriting_validation.db.models import Contact
        
        return and_(
            Contact.id == bindparam('contact_id'),
            # Soft-delete filter - exclude deleted contacts
            or_(
                Contact.del_.is_(null()),
                Contact.del_ != True
            )
        )
    
    def create_fivetran_filter(self, model_class):
        """
        Create filter for Fivetran-synced tables to exclude deleted records.
        
        Args:
            model_class: SQLAlchemy model class with _fivetran_deleted field
            
        Returns:
            SQLAlchemy filter condition
        """
        return or_(
            model_class._fivetran_deleted.is_(null()),
            model_class._fivetran_deleted == False
        )
    
    async def execute_single_result_query(
        self, 
        stmt, 
        contact_id: int, 
        operation_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Execute query expecting single result with standardized logging.
        
        Args:
            stmt: SQLAlchemy statement to execute
            contact_id: Contact ID for logging and parameters
            operation_name: Name of operation for logging
            
        Returns:
            Dictionary of result data or None if not found
        """
        self.log_query_start(contact_id, operation_name)
        
        try:
            result = await self.session.execute(stmt, {"contact_id": contact_id})
            row = result.fetchone()
            
            if row:
                self.log_query_result(contact_id, operation_name, True)
                # Convert row to dictionary
                return dict(row._mapping)
            else:
                self.log_query_result(contact_id, operation_name, False)
                return None
                
        except Exception as e:
            masked_id = mask_contact_id(contact_id)
            self.logger.error(f"Error in {operation_name} for contact {masked_id}: {e}")
            raise
    
    async def execute_multiple_result_query(
        self, 
        stmt, 
        contact_id: int, 
        operation_name: str
    ) -> List[Dict[str, Any]]:
        """
        Execute query expecting multiple results with standardized logging.
        
        Args:
            stmt: SQLAlchemy statement to execute
            contact_id: Contact ID for logging and parameters
            operation_name: Name of operation for logging
            
        Returns:
            List of result dictionaries
        """
        self.log_query_start(contact_id, operation_name)
        
        try:
            result = await self.session.execute(stmt, {"contact_id": contact_id})
            rows = result.fetchall()
            
            self.log_query_result(contact_id, operation_name, len(rows) > 0)
            
            # Convert rows to list of dictionaries
            return [dict(row._mapping) for row in rows]
                
        except Exception as e:
            masked_id = mask_contact_id(contact_id)
            self.logger.error(f"Error in {operation_name} for contact {masked_id}: {e}")
            raise
    
    def build_select_statement(self, base_model, joins: List = None, additional_filters: List = None):
        """
        Build a select statement with common patterns.
        
        Args:
            base_model: Base SQLAlchemy model to select from
            joins: List of (join_model, join_condition) tuples
            additional_filters: List of additional filter conditions
            
        Returns:
            SQLAlchemy select statement
        """
        # Start with base model
        stmt = select(base_model)
        
        # Add joins if specified
        if joins:
            for join_model, join_condition in joins:
                stmt = stmt.outerjoin(join_model, join_condition)
        
        # Add base contact filter
        filters = [self.create_base_contact_filter(None)]  # Will be bound later
        
        # Add additional filters
        if additional_filters:
            filters.extend(additional_filters)
        
        # Apply all filters
        stmt = stmt.where(and_(*filters))
        
        return stmt
    
    @abstractmethod
    def get_repository_type(self) -> str:
        """
        Get the repository type name.
        
        Returns:
            String identifying the repository type
        """
        pass


class ContractRepositoryBase(RepositoryBase):
    """
    Base class specifically for contract-related repositories.
    
    Provides common patterns used across contract validation repositories.
    """
    
    def __init__(self, session: AsyncSession, repository_name: str):
        super().__init__(session, repository_name)
    
    def calculate_match_result(self, value1: Any, value2: Any, field_name: str) -> str:
        """
        Calculate match result between two values.
        
        Args:
            value1: First value to compare
            value2: Second value to compare  
            field_name: Name of field being compared (for logging)
            
        Returns:
            "Match", "Mismatch", or "Missing Value"
        """
        # Handle None and empty string cases
        val1_empty = value1 is None or (isinstance(value1, str) and value1.strip() == '')
        val2_empty = value2 is None or (isinstance(value2, str) and value2.strip() == '')
        
        if val1_empty or val2_empty:
            return "Missing Value"
        
        # Normalize strings for comparison
        if isinstance(value1, str) and isinstance(value2, str):
            val1_norm = value1.strip().lower()
            val2_norm = value2.strip().lower()
            return "Match" if val1_norm == val2_norm else "Mismatch"
        
        # Direct comparison for non-strings
        return "Match" if value1 == value2 else "Mismatch"
    
    def validate_signature_format(self, signature: Optional[str]) -> str:
        """
        Validate signature format (no dots or dashes).
        
        Args:
            signature: Signature string to validate
            
        Returns:
            "Valid", "Invalid", or "Missing Value"
        """
        if not signature or signature.strip() == '':
            return "Missing Value"
        
        # Check for invalid characters
        invalid_chars = ['.', '-']
        if any(char in signature for char in invalid_chars):
            return "Invalid"
        
        return "Valid"
    
    def calculate_age_from_dob(self, date_of_birth) -> Optional[int]:
        """
        Calculate age from date of birth.
        
        Args:
            date_of_birth: Date of birth (date object or string)
            
        Returns:
            Age in years or None if invalid date
        """
        try:
            from datetime import datetime, date
            
            if isinstance(date_of_birth, str):
                birth_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            elif isinstance(date_of_birth, date):
                birth_date = date_of_birth
            else:
                return None
            
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
            
        except (ValueError, AttributeError):
            return None
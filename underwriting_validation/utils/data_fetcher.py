"""
Data Fetcher for Combined Validation Service

This module handles parallel database queries for all validation types.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from underwriting_validation.infrastructure.contact_repository import ContactRepository
from underwriting_validation.utils.pii_filter import mask_contact_id

logger = logging.getLogger(__name__)

class DataFetcher:
    """Handles parallel data fetching for validation services."""
    
    def __init__(self, repository: ContactRepository):
        self.repository = repository
        # Limit concurrent database operations to prevent connection pool exhaustion
        self.db_semaphore = asyncio.Semaphore(3)  # Reduced from 5 to 3 to prevent overwhelming the DB
    
    async def _fetch_with_semaphore(self, coro):
        """Execute a database operation with semaphore limiting."""
        async with self.db_semaphore:
            return await coro

    async def fetch_all_validation_data(
        self, 
        contact_id: int, 
        hardship_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Fetch all validation data in parallel for better performance.
        
        Args:
            contact_id: The contact ID to fetch data for
            hardship_data: Optional pre-fetched hardship data
            
        Returns:
            Tuple of (hardship_data, budget_data, address_data, contract_data, duplication_data, draft_data, credit_score_data)
        """
        masked_id = mask_contact_id(contact_id)
        
        # Prepare the list of coroutines to run in parallel
        data_fetch_tasks = []
        task_names = []
        
        # Add hardship data fetch if not provided
        if hardship_data is None:
            data_fetch_tasks.append(self._fetch_with_semaphore(self.repository.fetch_contact_with_hardship_data(contact_id)))
            task_names.append('hardship')
        else:
            data_fetch_tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Placeholder for hardship
            task_names.append('hardship (cached)')
        
        # Add other data fetches
        data_fetch_tasks.extend([
            self._fetch_with_semaphore(self.repository.fetch_contact_with_budget_data(contact_id)),
            self._fetch_with_semaphore(self.repository.fetch_contact_with_address_data(contact_id)),
            self._fetch_with_semaphore(self.repository.fetch_contact_with_contract_data(contact_id)),
            self._fetch_with_semaphore(self.repository.fetch_contact_with_duplication_data(contact_id)),
            self._fetch_with_semaphore(self.repository.fetch_contact_with_draft_data(contact_id)),
            self._fetch_with_semaphore(self.repository.fetch_contact_with_credit_score_data(contact_id))
        ])
        task_names.extend(['budget', 'address', 'contract', 'duplication', 'draft', 'credit_score'])
        
        # Execute all database queries in parallel
        logger.info(f"Fetching data for contact {masked_id} in parallel...")
        start_time = asyncio.get_event_loop().time()
        
        try:
            results = await asyncio.gather(*data_fetch_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error during parallel data fetching for contact {masked_id}: {e}")
            # Return None for all results on error
            results = [None] * len(data_fetch_tasks)
        
        end_time = asyncio.get_event_loop().time()
        fetch_time = end_time - start_time
        logger.info(f"Data fetching completed for contact {masked_id} in {fetch_time:.2f} seconds")
        
        # Extract results, handling the case where hardship_data might already be provided
        if hardship_data is None:
            hardship_data = results[0] if not isinstance(results[0], Exception) else None
            budget_data = results[1] if not isinstance(results[1], Exception) else None
            address_data = results[2] if not isinstance(results[2], Exception) else None
            contract_data = results[3] if not isinstance(results[3], Exception) else None
            duplication_data = results[4] if not isinstance(results[4], Exception) else None
            draft_data = results[5] if not isinstance(results[5], Exception) else None
            credit_score_data = results[6] if not isinstance(results[6], Exception) else None
        else:
            budget_data = results[0] if not isinstance(results[0], Exception) else None
            address_data = results[1] if not isinstance(results[1], Exception) else None
            contract_data = results[2] if not isinstance(results[2], Exception) else None
            duplication_data = results[3] if not isinstance(results[3], Exception) else None
            draft_data = results[4] if not isinstance(results[4], Exception) else None
            credit_score_data = results[5] if not isinstance(results[5], Exception) else None
        
        # Log any database query errors and timing
        for i, (result, task_name) in enumerate(zip(results, task_names)):
            if isinstance(result, Exception):
                logger.error(f"Database query '{task_name}' failed for contact {masked_id}: {result}")
            elif result is None:
                logger.warning(f"Database query '{task_name}' returned None for contact {masked_id}")
            else:
                logger.debug(f"Database query '{task_name}' completed successfully for contact {masked_id}")
        
        logger.info(f"Data fetching completed for contact {masked_id}")
        
        return hardship_data, budget_data, address_data, contract_data, duplication_data, draft_data, credit_score_data
    
    def check_data_availability(
        self, 
        hardship_data: Optional[Dict[str, Any]], 
        budget_data: Optional[Dict[str, Any]], 
        address_data: Optional[Dict[str, Any]], 
        contract_data: Optional[Dict[str, Any]], 
        duplication_data: Optional[Dict[str, Any]],
        draft_data: Optional[Dict[str, Any]],
        credit_score_data: Optional[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """
        Check which validation data is available.
        
        Returns:
            Dictionary with boolean flags for each data type
        """
        has_hardship_data = hardship_data and any([
            hardship_data.get('financial_hardship'),
            hardship_data.get('hardship_description')
        ])
        
        has_budget_data = budget_data and any([
            budget_data.get('total_net_income', 0) > 0,
            budget_data.get('total_expenses', 0) > 0
        ])
        
        has_address_data = address_data and any([
            address_data.get('state'),
            address_data.get('assigned_company')
        ])
        
        has_contract_data = contract_data and any([
            contract_data.get('sender_ip_address'),
            contract_data.get('signer_ip_address'),
            contract_data.get('forth_email'),
            contract_data.get('contract_email'),
            contract_data.get('client_signature'),
            contract_data.get('coclient_signature'),
            contract_data.get('contract_account_number'),
            contract_data.get('forth_account_number'),
            contract_data.get('contract_routing_number'),
            contract_data.get('forth_routing_number'),
            contract_data.get('contract_bank_name'),
            contract_data.get('forth_bank_name'),
            contract_data.get('contract_account_type'),
            contract_data.get('forth_account_type'),
            contract_data.get('contract_address'),
            contract_data.get('forth_address')
        ])
        
        has_duplication_data = duplication_data and not duplication_data.get("error")
        
        has_draft_data = draft_data and draft_data.get('months_with_data', 0) > 0
        
        has_credit_score_data = credit_score_data and credit_score_data.get('has_credit_data', False)
        
        return {
            'hardship': has_hardship_data,
            'budget': has_budget_data,
            'address': has_address_data,
            'contract': has_contract_data,
            'duplication': has_duplication_data,
            'draft': has_draft_data,
            'credit_score': has_credit_score_data
        }

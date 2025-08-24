"""
FIXED: Proper Session Management Patterns

This file shows the corrected patterns for session management to prevent memory leaks.
"""

from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

# ✅ SOLUTION 1: Repository Base with Proper Session Lifecycle
class FixedRepositoryBase:
    """Fixed repository base that doesn't hold session references."""
    
    def __init__(self, repository_name: str):
        """Initialize repository without storing session."""
        self.repository_name = repository_name
        self.logger = logging.getLogger(f"{__name__}.{repository_name}")
    
    async def execute_with_session(self, session: AsyncSession, operation, *args, **kwargs):
        """Execute operation with provided session - no session storage."""
        try:
            return await operation(session, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in {self.repository_name}: {e}")
            raise

# ✅ SOLUTION 2: Fixed Contract Repository (No Session Storage)
class FixedContractRepository(FixedRepositoryBase):
    """Fixed contract repository that doesn't store sessions."""
    
    def __init__(self):
        super().__init__("FixedContractRepository")
    
    async def fetch_contact_with_contract_data(
        self, 
        session: AsyncSession, 
        contact_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch contract data using provided session."""
        
        # ✅ Create specialized repos without session storage
        async def fetch_all_data():
            # Execute all queries concurrently with same session
            import asyncio
            
            results = await asyncio.gather(
                self._fetch_ip_data(session, contact_id),
                self._fetch_email_data(session, contact_id),
                self._fetch_signature_data(session, contact_id),
                self._fetch_bank_data(session, contact_id),
                # ... other data fetches
                return_exceptions=True
            )
            
            # Process results
            ip_data, email_data, signature_data, bank_data = results[:4]
            
            # Return combined data
            return {
                "contact_id": contact_id,
                "ip_data": ip_data if not isinstance(ip_data, Exception) else None,
                "email_data": email_data if not isinstance(email_data, Exception) else None,
                "signature_data": signature_data if not isinstance(signature_data, Exception) else None,
                "bank_data": bank_data if not isinstance(bank_data, Exception) else None,
            }
        
        return await self.execute_with_session(session, fetch_all_data)
    
    async def _fetch_ip_data(self, session: AsyncSession, contact_id: int):
        """Fetch IP data with provided session."""
        # Implementation here - no session storage
        pass
    
    async def _fetch_email_data(self, session: AsyncSession, contact_id: int):
        """Fetch email data with provided session."""
        # Implementation here - no session storage  
        pass

# ✅ SOLUTION 3: Fixed Service Layer (Session Per Operation)
class FixedCombinedValidationService:
    """Fixed service that uses session per operation pattern."""
    
    def __init__(self, hardship_service, budget_service, address_service, contract_service):
        # ✅ No repository stored - use dependency injection
        self.hardship_service = hardship_service
        self.budget_service = budget_service
        self.address_service = address_service
        self.contract_service = contract_service
        
    async def perform_combined_validation(
        self,
        session: AsyncSession,  # ✅ Session provided by caller
        contact_id: int
    ) -> Optional[Dict[str, Any]]:
        """Perform validation using provided session."""
        
        # ✅ Use single session for all operations in this request
        contract_repo = FixedContractRepository()
        
        try:
            # ✅ All operations use the same session - no session storage
            eligibility_data = await self._check_eligibility(session, contact_id)
            if not eligibility_data:
                return {"error": "Not eligible"}
            
            # ✅ Concurrent data fetching with same session
            import asyncio
            hardship_data, budget_data, address_data, contract_data = await asyncio.gather(
                self._fetch_hardship_data(session, contact_id),
                self._fetch_budget_data(session, contact_id), 
                self._fetch_address_data(session, contact_id),
                contract_repo.fetch_contact_with_contract_data(session, contact_id),
                return_exceptions=True
            )
            
            # Process and return results
            return {
                "contact_id": contact_id,
                "hardship_data": hardship_data if not isinstance(hardship_data, Exception) else None,
                "budget_data": budget_data if not isinstance(budget_data, Exception) else None,
                "address_data": address_data if not isinstance(address_data, Exception) else None,
                "contract_data": contract_data if not isinstance(contract_data, Exception) else None,
            }
            
        except Exception as e:
            logger.error(f"Error in combined validation: {e}")
            raise

    async def _check_eligibility(self, session: AsyncSession, contact_id: int):
        """Check eligibility using provided session."""
        # Implementation using session parameter
        pass
    
    async def _fetch_hardship_data(self, session: AsyncSession, contact_id: int):
        """Fetch hardship data using provided session."""
        # Implementation using session parameter
        pass
    
    async def _fetch_budget_data(self, session: AsyncSession, contact_id: int):
        """Fetch budget data using provided session."""
        # Implementation using session parameter
        pass
    
    async def _fetch_address_data(self, session: AsyncSession, contact_id: int):
        """Fetch address data using provided session."""
        # Implementation using session parameter
        pass

# ✅ SOLUTION 4: Fixed Dependency Injection (No Singletons)
class FixedDependencyInjection:
    """Fixed DI that doesn't cache services with state."""
    
    @staticmethod
    def create_validation_service() -> FixedCombinedValidationService:
        """Create new service instance (no caching)."""
        # ✅ Create fresh instances - no @lru_cache
        hardship_service = HardshipValidationService()
        budget_service = BudgetValidationService()
        address_service = AddressValidationService()
        contract_service = ContractValidationService()
        
        return FixedCombinedValidationService(
            hardship_service, budget_service, address_service, contract_service
        )
    
    @staticmethod
    async def get_validation_service_with_session(
        session: AsyncSession
    ) -> FixedCombinedValidationService:
        """Get service with session dependency injection."""
        # ✅ Session passed to service methods, not stored
        return FixedDependencyInjection.create_validation_service()

# ✅ SOLUTION 5: Fixed Session Context Manager
@asynccontextmanager
async def fixed_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Fixed session context manager with proper cleanup."""
    session = None
    try:
        # ✅ Create session
        session = AsyncSession()
        
        # ✅ Yield session for use
        yield session
        
        # ✅ Commit transaction
        await session.commit()
        
    except Exception as e:
        # ✅ Rollback on error
        if session:
            await session.rollback()
        logger.error(f"Session error: {e}")
        raise
    finally:
        # ✅ Always close session
        if session:
            await session.close()
            session = None  # ✅ Clear reference

# ✅ SOLUTION 6: Fixed API Endpoint Pattern
async def fixed_api_endpoint(contact_id: int):
    """Fixed API endpoint with proper session management."""
    
    # ✅ Session scope limited to this request
    async with fixed_db_session_context() as session:
        # ✅ Create service without storing session
        service = FixedDependencyInjection.create_validation_service()
        
        # ✅ Pass session to service operation
        result = await service.perform_combined_validation(session, contact_id)
        
        # ✅ Session automatically closed when context exits
        return result

# ✅ SOLUTION 7: Fixed Connection Pool Settings
FIXED_POOL_SETTINGS = {
    "pool_size": 20,           # ✅ Increased for concurrency
    "max_overflow": 30,        # ✅ Higher overflow for spikes  
    "pool_timeout": 10,        # ✅ Shorter timeout to detect issues quickly
    "pool_recycle": 300,       # ✅ 5-minute recycle for fresh connections
    "pool_pre_ping": True,     # ✅ Test connections before use
}

# ✅ SOLUTION 8: Fixed Connection Pool Warming
async def fixed_warm_connection_pool(target_connections: int = 5) -> bool:
    """Fixed connection pool warming without memory leaks."""
    
    successful_connections = 0
    
    for i in range(target_connections):
        try:
            # ✅ Create and immediately close session
            async with fixed_db_session_context() as session:
                await session.execute(text("SELECT 1"))
                successful_connections += 1
                
        except Exception as e:
            logger.warning(f"Failed to warm connection {i}: {e}")
            # ✅ Continue with other connections
            continue
    
    logger.info(f"Warmed {successful_connections}/{target_connections} connections")
    return successful_connections > 0
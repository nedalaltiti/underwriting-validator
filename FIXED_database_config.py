"""
FIXED: Database Configuration to Prevent Memory Leaks

This shows the corrected database configuration settings.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import QueuePool
import logging
import os

logger = logging.getLogger(__name__)

# ❌ ORIGINAL PROBLEMATIC SETTINGS
BROKEN_SETTINGS = {
    "pool_size": 5,           # ❌ Too small for concurrent requests
    "max_overflow": 10,       # ❌ Creates connection churn
    "pool_timeout": 30,       # ❌ Long timeout masks pool exhaustion  
    "pool_recycle": 1800,     # ❌ 30min allows stale connections
    "pool_pre_ping": False,   # ❌ No connection health checks
}

# ✅ FIXED OPTIMAL SETTINGS
FIXED_SETTINGS = {
    # ✅ Connection Pool Sizing
    "pool_size": 20,          # ✅ Base connections for normal load
    "max_overflow": 30,       # ✅ Overflow for traffic spikes (total: 50 connections)
    
    # ✅ Timeout Settings  
    "pool_timeout": 10,       # ✅ Quick timeout to detect pool issues
    "pool_recycle": 300,      # ✅ 5min recycle for fresh connections
    
    # ✅ Health & Performance
    "pool_pre_ping": True,    # ✅ Test connections before use
    "echo": False,            # ✅ Disable SQL logging in production
    
    # ✅ Additional SQLAlchemy Settings
    "connect_args": {
        "command_timeout": 30,        # ✅ Query timeout
        "server_settings": {
            "application_name": "underwriting_validation",  # ✅ Identify connections
            "jit": "off",             # ✅ Disable JIT for consistent performance
        }
    }
}

# ✅ FIXED ENGINE CREATION
def create_fixed_engine(database_url: str):
    """Create database engine with optimal settings."""
    
    return create_async_engine(
        database_url,
        
        # ✅ Connection Pool Settings
        poolclass=QueuePool,
        pool_size=FIXED_SETTINGS["pool_size"],
        max_overflow=FIXED_SETTINGS["max_overflow"],
        pool_timeout=FIXED_SETTINGS["pool_timeout"],
        pool_recycle=FIXED_SETTINGS["pool_recycle"],
        pool_pre_ping=FIXED_SETTINGS["pool_pre_ping"],
        
        # ✅ Performance Settings
        echo=FIXED_SETTINGS["echo"],
        connect_args=FIXED_SETTINGS["connect_args"],
        
        # ✅ Additional Optimizations
        future=True,              # ✅ Use SQLAlchemy 2.0 style
        query_cache_size=1200,    # ✅ Cache compiled queries
    )

# ✅ FIXED SESSION FACTORY
def create_fixed_session_factory(engine):
    """Create session factory with optimal settings."""
    
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        
        # ✅ Session Settings
        expire_on_commit=False,   # ✅ Don't expire objects after commit
        autoflush=True,           # ✅ Auto-flush before queries
        autocommit=False,         # ✅ Manual transaction control
    )

# ✅ FIXED SESSION DEPENDENCY
from typing import AsyncGenerator
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_fixed_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixed database session dependency with proper lifecycle management.
    
    This prevents memory leaks by ensuring sessions are always closed.
    """
    session = None
    try:
        # ✅ Create session from factory
        session = AsyncSession()
        
        # ✅ Yield session for request handling
        yield session
        
        # ✅ Commit successful transactions
        await session.commit()
        
    except Exception as e:
        # ✅ Rollback failed transactions
        if session:
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}")
        
        logger.error(f"Database session error: {e}")
        raise
        
    finally:
        # ✅ CRITICAL: Always close session
        if session:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Error closing session: {close_error}")
            finally:
                session = None  # ✅ Clear reference

# ✅ FIXED FASTAPI DEPENDENCY
async def get_db_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with get_fixed_db_session() as session:
        yield session

# ✅ FIXED CONNECTION POOL MONITORING
async def get_connection_pool_status(engine):
    """Get connection pool status for monitoring."""
    
    pool = engine.pool
    
    return {
        # Pool Configuration
        "pool_size": pool.size(),
        "max_overflow": pool.overflow(),
        
        # Current Usage
        "checked_out": pool.checkedout(),
        "checked_in": pool.checkedin(),
        "total_available": pool.checkedin(),
        
        # Health Metrics
        "utilization_percent": round(
            (pool.checkedout() / (pool.size() + pool.overflow())) * 100, 1
        ) if (pool.size() + pool.overflow()) > 0 else 0,
        
        # Alerts
        "is_pool_exhausted": pool.checkedout() >= (pool.size() + pool.overflow()),
        "high_utilization": (pool.checkedout() / (pool.size() + pool.overflow())) > 0.8,
    }

# ✅ FIXED CONNECTION POOL WARMING (No Memory Leaks)
async def fixed_warm_connection_pool(engine, target_connections: int = 5) -> bool:
    """Warm connection pool without memory leaks."""
    
    successful_connections = 0
    
    for i in range(target_connections):
        try:
            # ✅ Use proper session lifecycle
            async with get_fixed_db_session() as session:
                # ✅ Simple health check
                result = await session.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                
                if row and row.health_check == 1:
                    successful_connections += 1
                    
        except Exception as e:
            logger.warning(f"Failed to warm connection {i+1}: {e}")
            # ✅ Continue with remaining connections
            continue
    
    logger.info(f"Successfully warmed {successful_connections}/{target_connections} connections")
    return successful_connections > 0

# ✅ ENVIRONMENT VARIABLES FOR CONFIGURATION
def get_database_config_from_env():
    """Get database configuration from environment variables."""
    
    return {
        # ✅ Connection Settings
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME", "underwriting"),
        "username": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        
        # ✅ Pool Settings (can be overridden via environment)
        "pool_size": int(os.getenv("DB_POOL_SIZE", FIXED_SETTINGS["pool_size"])),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", FIXED_SETTINGS["max_overflow"])),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", FIXED_SETTINGS["pool_timeout"])),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", FIXED_SETTINGS["pool_recycle"])),
    }

# ✅ COMPLETE FIXED DATABASE SETUP
async def setup_fixed_database():
    """Complete database setup with all fixes applied."""
    
    # ✅ Get configuration
    config = get_database_config_from_env()
    
    # ✅ Build connection URL
    database_url = f"postgresql+asyncpg://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    
    # ✅ Create engine with fixed settings
    engine = create_fixed_engine(database_url)
    
    # ✅ Create session factory
    SessionFactory = create_fixed_session_factory(engine)
    
    # ✅ Test connection
    try:
        async with get_fixed_db_session() as session:
            await session.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful")
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        raise
    
    # ✅ Warm connection pool
    warmed = await fixed_warm_connection_pool(engine, target_connections=3)
    if warmed:
        logger.info("✅ Connection pool warmed successfully")
    else:
        logger.warning("⚠️ Connection pool warming failed")
    
    return engine, SessionFactory

# ✅ USAGE EXAMPLE
"""
# In your application startup:
engine, SessionFactory = await setup_fixed_database()

# In your FastAPI app:
@app.get("/validate/{contact_id}")
async def validate_contact(
    contact_id: int,
    session: AsyncSession = Depends(get_db_session_dependency)
):
    # ✅ Session automatically managed
    repo = FixedContractRepository()
    result = await repo.fetch_contact_with_contract_data(session, contact_id)
    return result
    # ✅ Session automatically closed
"""
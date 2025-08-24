"""
FastAPI application entry-point.

All runtime wiring (middleware, routers, startup/shutdown) lives here so tests
can import `app` without side-effects.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio
import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from underwriting_validation.api.routers import admin, health, debug, validation
from underwriting_validation.config.settings import settings
from underwriting_validation.utils.error import BaseError, ErrorSeverity
from underwriting_validation.services.gemini_service import GeminiService
from underwriting_validation.services.contact_service import InvalidContactIDError, ContactNotFoundError
from underwriting_validation.utils.pii_filter import setup_pii_filtering
from underwriting_validation.utils.rate_limiter import get_rate_limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Set up PII filtering for all loggers
setup_pii_filtering()

logger = logging.getLogger("underwritting_validation.app")

# Store temporary credentials path for cleanup
_temp_credentials_path = None

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise expensive singletons once per process and dispose on exit."""
    global _temp_credentials_path
    
    logger.info("Underwriting Validation API starting up…")

    # Validate hardship field configuration
    try:
        hardship_fields = settings.hardship_fields
        logger.info(f"Validating hardship field configuration...")
        logger.info(f"  Financial hardship ID: {hardship_fields.financial_hardship_id}")
        logger.info(f"  Hardship description ID: {hardship_fields.hardship_description_id}")
        
        if not hardship_fields.validate():
            raise ValueError("Invalid hardship field configuration detected during startup")
        
        logger.info("✅ Hardship field configuration validated successfully")
    except Exception as e:
        logger.error(f"Hardship field validation failed: {e}")
        raise

    # Validate budget field configuration
    try:
        budget_fields = settings.budget_fields
        logger.info(f"Validating budget field configuration...")
        logger.info(f"  Budget uses base query settings")
        logger.info(f"  Base query acctid: {settings.base_query.acctid}")
        logger.info(f"  Base query c_type: {settings.base_query.c_type}")
        logger.info(f"  Base query iscoapp: {settings.base_query.iscoapp}")
        logger.info(f"  Base query leadstatus: {settings.base_query.leadstatus}")
        
        if not budget_fields.validate():
            raise ValueError("Invalid budget field configuration detected during startup")
        
        logger.info("✅ Budget field configuration validated successfully")
    except Exception as e:
        logger.error(f"Budget field validation failed: {e}")
        raise

    # Validate address field configuration
    try:
        address_fields = settings.address_fields
        logger.info(f"Validating address field configuration...")
        logger.info(f"  Address uses base query settings")
        logger.info(f"  Base query acctid: {settings.base_query.acctid}")
        logger.info(f"  Base query c_type: {settings.base_query.c_type}")
        logger.info(f"  Base query iscoapp: {settings.base_query.iscoapp}")
        logger.info(f"  Base query leadstatus: {settings.base_query.leadstatus}")
        logger.info(f"  Address company_type: {address_fields.company_type}")
        
        if not address_fields.validate():
            raise ValueError("Invalid address field configuration detected during startup")
        
        logger.info("✅ Address field configuration validated successfully")
    except Exception as e:
        logger.error(f"Address field validation failed: {e}")
        raise

    # Initialize database connections first
    try:
        from underwriting_validation.db.session import init_database
        await init_database()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Check if we should fail on DB errors
        if os.environ.get("SKIP_DB_INIT", "").lower() not in ("true", "1", "yes"):
            raise
        else:
            logger.warning("Continuing without database (SKIP_DB_INIT=true)")

    # Store temporary credentials path for cleanup
        _temp_credentials_path = settings.gemini.credentials_path

    # Initialize LLM service in background to reduce first-request latency
    asyncio.create_task(_warmup_services())



    logger.info("✅  Startup complete")
    try:
        yield
    finally:
        logger.info("👋  Shutting down...")
        
        # Clean up database connections
        try:
            from underwriting_validation.db.session import close_database
            await close_database()
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
        logger.info("👋  Goodbye")


async def _warmup_services():
    """Warm up LLM service in the background."""
    try:
        # Initialize Gemini
        logger.info("Warming up Gemini service...")
        gemini = GeminiService()
        await gemini.test_connection()
        
        logger.info("Service warmup complete")
    except Exception as e:
        logger.warning(f"Service warmup failed (non-critical): {e}")


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    redirect_slashes=False,
)

# Add rate limiter middleware
limiter = get_rate_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if settings.cors_origins:   # don't enable CORS unless explicitly configured
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(validation.router, prefix="/api/validation", tags=["validation"])
app.include_router(admin.router,  prefix="/api/admin", tags=["admin"])
app.include_router(debug.router, prefix="/api/debug", tags=["debug"])

@app.exception_handler(BaseError)
async def Underwriting_error_handler(_: Request, exc: BaseError) -> JSONResponse:
    """Return structured JSON for domain errors; fall back to FastAPI default
    for everything else.
    """
    status_code = (
        status.HTTP_400_BAD_REQUEST
        if exc.severity in {ErrorSeverity.INFO, ErrorSeverity.WARNING}
        else status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    return JSONResponse(status_code=status_code, content=exc.to_dict())

@app.exception_handler(InvalidContactIDError)
async def invalid_contact_id_handler(_: Request, exc: InvalidContactIDError) -> JSONResponse:
    """Handle invalid contact ID format errors with HTTP 422 Unprocessable Entity."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Invalid Contact ID Format",
            "message": str(exc),
            "type": "validation_error",
            "details": "Contact ID must be a positive integer with 1-11 digits"
        }
    )

@app.exception_handler(ContactNotFoundError)
async def contact_not_found_handler(_: Request, exc: ContactNotFoundError) -> JSONResponse:
    """Handle contact not found errors with HTTP 404 Not Found."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Contact Not Found",
            "message": str(exc),
            "type": "not_found_error",
            "details": "Contact ID is valid but not found in database"
        }
    )

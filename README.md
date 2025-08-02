# Underwriting Validation API

A pure API service for contact validation, providing hardship and budget analysis capabilities.

## Overview

Underwriting Validation API is a FastAPI-based service that provides contact validation functionality without any Teams or feedback-related components. It focuses purely on:

- Contact hardship validation
- Budget analysis
- Combined validation (hardship + budget)
- Database integration for contact data

## Features

- **Contact Validation**: Validate contacts for hardship and budget information
- **Combined Analysis**: Perform comprehensive validation combining both hardship and budget analysis
- **Database Integration**: PostgreSQL database integration for contact data
- **Gemini AI**: Google Gemini integration for AI-powered analysis
- **Health Monitoring**: Comprehensive health and diagnostic endpoints

## API Endpoints

### Validation Endpoints

- `POST /api/validation/contact` - Validate a contact for hardship and/or budget information
- `POST /api/validation/combined` - Perform combined hardship and budget validation
- `GET /api/validation/contact/{contact_id}` - Get basic contact information without validating

### Health Endpoints

- `GET /health` - Basic health check
- `GET /health/database` - Database-specific health check
- `GET /health/diagnostic` - Detailed diagnostic information

### Debug Endpoints

- `POST /api/debug/contact` - Debug contact validation

### Admin Endpoints

- `GET /api/admin/status` - Admin status information

## Configuration

The service uses environment variables for configuration:

### Database Configuration
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_HOST` - Database host
- `DB_PORT` - Database port (default: 5432)

### Gemini Configuration
- `GOOGLE_API_KEY` - Google API key for Gemini
- `GEMINI_MODEL_NAME` - Gemini model name (default: gemini-2.0-flash-001)
- `GEMINI_TEMPERATURE` - Gemini temperature setting (default: 0.0)

### Application Configuration
- `APP_NAME` - Application name (default: "Underwriting Validation API")
- `HOST` - Host to bind to (default: 0.0.0.0)
- `PORT` - Port to bind to (default: 3978)
- `DEBUG` - Enable debug mode (default: false)

### Field Configuration
- `HARDSHIP_FINANCIAL_ID` - Financial hardship field ID
- `HARDSHIP_DESCRIPTION_ID` - Hardship description field ID
- `BUDGET_ACCTID` - Budget account ID field
- `BUDGET_C_TYPE` - Budget contact type field
- `BUDGET_ISCOAPP` - Budget iscoapp field
- `BUDGET_LEADSTATUS` - Budget lead status field

## Running the Service

### Prerequisites

Install dependencies using Poetry:
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### Development
```bash
# Using Poetry
poetry run python -m underwriting_validation.api

# Or activate the virtual environment first
poetry shell
python -m underwriting_validation.api

# Or use the Poetry script
poetry run underwriting-api
```

### Production
```bash
# Using Poetry
poetry run uvicorn underwriting_validation.api.app:app --host 0.0.0.0 --port 3978

# Or traditional uvicorn (after poetry install)
uvicorn underwriting_validation.api.app:app --host 0.0.0.0 --port 3978
```

### Docker (Recommended)
```bash
# Development with Docker Compose
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up --build
```

## API Documentation

Once the service is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:3978/docs`
- ReDoc: `http://localhost:3978/redoc`

## Example Usage

### Validate a Contact
```bash
curl -X POST "http://localhost:3978/api/validation/contact" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": 12345,
    "include_budget": true,
    "include_hardship": true
  }'
```

### Combined Validation
```bash
curl -X POST "http://localhost:3978/api/validation/combined" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": 12345
  }'
```

## Architecture

The service follows a clean architecture pattern:

- **API Layer**: FastAPI routers and endpoints
- **Service Layer**: Business logic for validation
- **Repository Layer**: Data access and database operations
- **Infrastructure Layer**: External service integrations (Gemini)

## Dependencies

- FastAPI - Web framework
- SQLAlchemy - Database ORM
- asyncpg - PostgreSQL async driver
- Google Generative AI - Gemini integration
- Pydantic - Data validation

## License

This project is proprietary and confidential. 
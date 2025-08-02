# Docker Setup Guide - Using Poetry

This guide shows how to run the Underwriting Validation API using Docker with Poetry dependency management.

## Quick Start

### 1. Build and Run with Docker Compose (Development)

```bash
# Create environment file (copy and modify the example)
cp .env.example .env
# Edit .env with your actual values (especially GOOGLE_API_KEY)

# Build and start services
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### 2. Production Deployment

```bash
# Set up production environment variables
export GOOGLE_API_KEY="your_actual_api_key"
export DB_HOST="your_production_db_host"
export DB_NAME="your_production_db_name"
export DB_USER="your_production_db_user"
export DB_PASSWORD="your_production_db_password"
export HARDSHIP_FINANCIAL_ID="your_field_id"
export HARDSHIP_DESCRIPTION_ID="your_field_id"
export BUDGET_ACCTID="your_field_id"
export BUDGET_C_TYPE="your_field_id"
export BUDGET_ISCOAPP="your_field_id"
export BUDGET_LEADSTATUS="your_field_id"

# Deploy using production compose file
docker-compose -f docker-compose.prod.yml up --build -d
```

## Local Development (Without Docker)

### Using Poetry

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run the application
poetry run python -m underwriting_validation.api

# Or activate the shell and run directly
poetry shell
python -m underwriting_validation.api

# Or use the defined script
poetry run underwriting-api
```

## Docker Architecture

### Multi-stage Build
- **Builder Stage**: Uses Poetry to install dependencies in a virtual environment
- **Runtime Stage**: Copies only the virtual environment and application code for a smaller final image

### Features
- ✅ Poetry dependency management
- ✅ Multi-stage build for smaller images
- ✅ Non-root user for security
- ✅ Health checks
- ✅ PostgreSQL database included in development setup
- ✅ Volume mounts for development hot-reload
- ✅ Production-ready configuration

## Environment Variables

Required environment variables:

```bash
# Database (Required)
DB_HOST=postgres          # or your database host
DB_NAME=underwriting_db
DB_USER=underwriting_user
DB_PASSWORD=your_password

# Google API (Required)
GOOGLE_API_KEY=your_google_api_key

# Field Configuration (Required)
HARDSHIP_FINANCIAL_ID=1
HARDSHIP_DESCRIPTION_ID=2
BUDGET_ACCTID=3
BUDGET_C_TYPE=4
BUDGET_ISCOAPP=5
BUDGET_LEADSTATUS=6
```

## Useful Commands

```bash
# View logs
docker-compose logs -f underwriting-api

# Stop services
docker-compose down

# Rebuild without cache
docker-compose build --no-cache

# Run a specific service
docker-compose up postgres  # Only database

# Execute commands in running container
docker-compose exec underwriting-api bash

# Check health status
docker-compose ps
```

## API Access

Once running, access:
- **API Documentation**: http://localhost:3978/docs
- **Health Check**: http://localhost:3978/health
- **Database Health**: http://localhost:3978/health/database

## Troubleshooting

### Common Issues

1. **Poetry Lock File Missing**
   ```bash
   # Generate poetry.lock file
   poetry lock
   ```

2. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

3. **Database Connection Issues**
   - Ensure PostgreSQL service is healthy
   - Check environment variables
   - Verify network connectivity

4. **Build Issues**
   ```bash
   # Clean build
   docker-compose down
   docker system prune -f
   docker-compose build --no-cache
   ```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs underwriting-api
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f underwriting-api
```
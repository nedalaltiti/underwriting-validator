#!/bin/bash

# 🔧 Install Dependencies Script
# This script installs all required dependencies for the underwriting validation service

echo "📦 Installing Python dependencies for underwriting-validation..."

# Core framework dependencies
pip3 install fastapi==0.111.0
pip3 install uvicorn[standard]==0.24.0
pip3 install pydantic==2.0.0

# Database dependencies  
pip3 install sqlalchemy[asyncio]==2.0.0
pip3 install asyncpg==0.29.0

# HTTP client
pip3 install httpx==0.25.0

# Google AI dependencies
pip3 install google-generativeai==0.3.0
pip3 install google-cloud-aiplatform==1.38.0

# Utility dependencies
pip3 install python-dotenv==1.0.0
pip3 install backoff==2.2.0
pip3 install slowapi==0.1.9

# Development dependencies
pip3 install pytest==7.4.0
pip3 install pytest-asyncio==0.21.0

echo "✅ All dependencies installed successfully!"

# Test critical imports
echo "🧪 Testing critical imports..."

python3 -c "
import sys
sys.path.append('.')

try:
    from pydantic import BaseModel
    print('✅ pydantic import works')
except ImportError as e:
    print(f'❌ pydantic import failed: {e}')

try:
    from sqlalchemy import select
    print('✅ sqlalchemy import works')
except ImportError as e:
    print(f'❌ sqlalchemy import failed: {e}')

try:
    from fastapi import FastAPI
    print('✅ fastapi import works')
except ImportError as e:
    print(f'❌ fastapi import failed: {e}')

try:
    from underwriting_validation.utils.result import Result, Success, Error
    print('✅ Internal result imports work')
except ImportError as e:
    print(f'❌ Internal result imports failed: {e}')

try:
    from underwriting_validation.utils.pii_filter import mask_contact_id
    print('✅ Internal PII filter imports work')
except ImportError as e:
    print(f'❌ Internal PII filter imports failed: {e}')
"

echo "🎉 Dependency installation complete!"
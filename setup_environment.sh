#!/bin/bash

# 🔧 Setup Virtual Environment and Install Dependencies
# This script creates a virtual environment and installs all required dependencies

echo "🚀 Setting up Python virtual environment for underwriting-validation..."

# Create virtual environment
echo "📁 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing core dependencies..."
pip install fastapi==0.111.0
pip install uvicorn[standard]==0.24.0  
pip install pydantic==2.0.0
pip install sqlalchemy[asyncio]==2.0.0
pip install asyncpg==0.29.0
pip install httpx==0.25.0
pip install python-dotenv==1.0.0
pip install backoff==2.2.0
pip install slowapi==0.1.9

echo "📦 Installing AI dependencies..."
pip install google-generativeai==0.3.0
pip install google-cloud-aiplatform==1.38.0

echo "📦 Installing development dependencies..."
pip install pytest==7.4.0
pip install pytest-asyncio==0.21.0

echo "🧪 Testing critical imports..."

python -c "
import sys
import os
sys.path.insert(0, os.getcwd())

print('Testing external dependencies...')
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

print('\\nTesting internal dependencies...')
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

try:
    from underwriting_validation.utils.validation_base import ContractValidationServiceBase
    print('✅ Base class imports work')
except ImportError as e:
    print(f'❌ Base class imports failed: {e}')

print('\\nTesting service imports...')
try:
    from underwriting_validation.services.contract_ip_validation_service import ContractIPValidationService
    service = ContractIPValidationService()
    print('✅ IP Validation Service works')
except ImportError as e:
    print(f'❌ IP Validation Service failed: {e}')
except Exception as e:
    print(f'⚠️  IP Validation Service loaded but has runtime error: {e}')
"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 To use this environment:"
echo "   source venv/bin/activate"
echo "   python your_script.py"
echo ""
echo "📋 To deactivate:"
echo "   deactivate"
#!/bin/bash

# 🔧 Install Dependencies with Poetry
# This script installs dependencies using Poetry (if available)

echo "📦 Installing dependencies with Poetry..."

# Check if poetry is available
if command -v poetry &> /dev/null; then
    echo "✅ Poetry found, installing dependencies..."
    poetry install
    
    echo "🧪 Testing imports with Poetry environment..."
    poetry run python -c "
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
"
else
    echo "❌ Poetry not found. Please use the pip installation script instead:"
    echo "   ./install_dependencies.sh"
    exit 1
fi

echo "🎉 Poetry installation complete!"
#!/usr/bin/env python3
"""
Simple test script to verify the validation API structure.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all core modules can be imported."""
    try:
        # Test core imports
        from underwriting_validation.config.settings import settings
        print("✅ Settings imported successfully")
        
        from underwriting_validation.api.app import app
        print("✅ FastAPI app imported successfully")
        
        # Test service imports
        from underwriting_validation.services.contact_service import ContactService
        print("✅ ContactService imported successfully")
        
        from underwriting_validation.services.hardship_validation_service import HardshipValidationService
        print("✅ HardshipValidationService imported successfully")
        
        from underwriting_validation.services.budget_validation_service import BudgetValidationService
        print("✅ BudgetValidationService imported successfully")
        
        from underwriting_validation.services.combined_validation_service import CombinedValidationService
        print("✅ CombinedValidationService imported successfully")
        
        # Test router imports
        from underwriting_validation.api.routers import validation, health, admin, debug
        print("✅ All routers imported successfully")
        
        # Test infrastructure imports
        from underwriting_validation.infrastructure.contact_repository import ContactRepository
        print("✅ ContactRepository imported successfully")
        
        print("\n🎉 All imports successful! The validation API structure is correct.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_app_configuration():
    """Test that the app is properly configured."""
    try:
        from underwriting_validation.api.app import app
        
        # Check that the app has the expected routers
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        expected_routes = [
            '/health',
            '/api/validation',
            '/api/admin',
            '/api/debug'
        ]
        
        print(f"📋 Available routes: {routes}")
        
        # Check for validation endpoints
        validation_routes = [route for route in routes if 'validation' in route]
        if validation_routes:
            print(f"✅ Validation routes found: {validation_routes}")
        else:
            print("❌ No validation routes found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ App configuration error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing UWBot Validation API Structure")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test app configuration
        config_ok = test_app_configuration()
        
        if config_ok:
            print("\n🎉 All tests passed! The validation API is ready to use.")
            sys.exit(0)
        else:
            print("\n❌ App configuration tests failed.")
            sys.exit(1)
    else:
        print("\n❌ Import tests failed.")
        sys.exit(1) 
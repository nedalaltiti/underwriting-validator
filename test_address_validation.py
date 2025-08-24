#!/usr/bin/env python3
"""
Simple test script for address validation functionality.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from underwriting_validation.services.address_validation_service import AddressValidationService, AddressDataIn


async def test_address_validation():
    """Test the address validation service with sample data."""
    
    print("🧪 Testing Address Validation Service")
    print("=" * 50)
    
    # Initialize the service
    service = AddressValidationService()
    
    # Test cases
    test_cases = [
        {
            "name": "Valid Clarity Debt Resolution Assignment",
            "data": AddressDataIn(
                contact_id=12345,
                state="CA",
                assigned_company="Clarity Debt Resolution, Inc."
            )
        },
        {
            "name": "Valid Concordia Legal Advisors Assignment",
            "data": AddressDataIn(
                contact_id=12346,
                state="GA",
                assigned_company="Concordia Legal Advisors, PLLC"
            )
        },
        {
            "name": "Invalid State for Company",
            "data": AddressDataIn(
                contact_id=12347,
                state="CA",
                assigned_company="Concordia Legal Advisors, PLLC"  # Wrong company for CA
            )
        },
        {
            "name": "Invalid State",
            "data": AddressDataIn(
                contact_id=12348,
                state="XX",  # Invalid state
                assigned_company="Clarity Debt Resolution, Inc."
            )
        },
        {
            "name": "Missing Data",
            "data": AddressDataIn(
                contact_id=12349,
                state=None,
                assigned_company=None
            )
        },
        {
            "name": "Partial Data",
            "data": AddressDataIn(
                contact_id=12350,
                state="TX",
                assigned_company=None  # Missing company
            )
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        try:
            # Run the validation
            result = await service.analyze_address_validity(test_case['data'])
            
            if result.is_success():
                analysis = result.value
                print(f"✅ Result: {analysis.result.value.upper()}")
                print(f"📝 Reason: {analysis.reason}")
                print(f"🏛️  State Check: {analysis.state_check}")
                
                # Show the formatted response
                formatted = service.format_address_response(analysis, test_case['data'])
                print(f"\n📋 Formatted Response:")
                print(formatted)
            else:
                print(f"❌ Error: {result.error}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Address validation tests completed!")


if __name__ == "__main__":
    asyncio.run(test_address_validation())

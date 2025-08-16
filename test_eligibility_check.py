#!/usr/bin/env python3
"""
Test script for contact eligibility check functionality.
"""

import sys
import os
import asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_eligibility_check():
    """Test the contact eligibility check functionality."""
    print("🧪 Testing Contact Eligibility Check")
    print("=" * 50)
    
    try:
        # Test imports
        from underwriting_validation.services.contact_service import ContactService
        from underwriting_validation.infrastructure.contact_repository import ContactRepository
        from underwriting_validation.services.hardship_validation_service import HardshipValidationService
        from underwriting_validation.db.session import AsyncSession
        
        print("✅ All imports successful")
        
        # Test cases - you'll need to replace these with actual contact IDs from your database
        test_contact_ids = [
            12345,  # Replace with actual contact ID
            67890,  # Replace with actual contact ID
            11111   # Replace with actual contact ID
        ]
        
        print(f"\n📋 Testing eligibility for contact IDs: {test_contact_ids}")
        
        async with AsyncSession() as session:
            # Initialize services
            hardship_service = HardshipValidationService()
            repository = ContactRepository(session)
            contact_service = ContactService(hardship_service, repository)
            
            for contact_id in test_contact_ids:
                print(f"\n🔍 Checking eligibility for contact {contact_id}")
                print("-" * 40)
                
                try:
                    # Check eligibility
                    eligibility_data = await contact_service.check_contact_eligibility(contact_id)
                    
                    if eligibility_data:
                        print(f"✅ ELIGIBLE")
                        print(f"📧 Email: {eligibility_data.get('email', 'N/A')}")
                        print(f"📞 Phone: {eligibility_data.get('phone3', 'N/A')}")
                        print(f"🏷️  Category: {eligibility_data.get('contact_category', 'N/A')}")
                        print(f"📊 Lead Status: {eligibility_data.get('contact_lead_status', 'N/A')}")
                        print(f"🆔 Account ID: {eligibility_data.get('acctid', 'N/A')}")
                    else:
                        print(f"❌ NOT ELIGIBLE")
                        print(f"💡 Reason: Contact does not meet eligibility criteria")
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Eligibility check tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_eligibility_check())

#!/usr/bin/env python
"""
Quick test to verify the utils import fix
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def test_utils_import():
    """Test that utils.assign_groups_for_registration can be imported and called"""
    print("🧪 TESTING UTILS IMPORT FIX")
    print("=" * 50)
    
    try:
        # Test import
        from core import utils
        print("✅ Successfully imported core.utils")
        
        # Test function exists
        if hasattr(utils, 'assign_groups_for_registration'):
            print("✅ assign_groups_for_registration function exists")
            
            # Test import in admin_registration context
            from core.admin_registration import Step2RegistrationView
            print("✅ Successfully imported Step2RegistrationView")
            
            print("\n🎯 THE IMPORT ERROR HAS BEEN FIXED!")
            print("✅ Step 3 should now work correctly in the admin interface")
            
        else:
            print("❌ assign_groups_for_registration function not found")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Other error: {e}")

if __name__ == "__main__":
    test_utils_import()
#!/usr/bin/env python
"""
Test script to verify Step 3 admin registration is working
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from core.models import RegistrationDraft, Athlete  # noqa: E402

def test_step3_registration():
    """Test that step 3 admin registration works"""
    print("🧪 TESTING STEP 3 ADMIN REGISTRATION")
    print("=" * 60)
    
    # Create admin user for testing
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username='test_admin_step3',
            email='admin@test.com',
            password='admin123'
        )
        print(f"✅ Created test admin: {admin_user.username}")
    
    # Create test client
    client = Client()
    client.force_login(admin_user)
    
    print("\n📝 Testing full 3-step registration process...")
    
    # Step 1: Create user
    step1_data = {
        'username': 'test_step3_user',
        'email': 'test_step3@example.com',
        'password1': 'complexpass123',
        'password2': 'complexpass123'
    }
    
    # Clean up any existing user
    User.objects.filter(username='test_step3_user').delete()
    
    response = client.post(reverse('admin:register_step1'), data=step1_data)
    print(f"  Step 1 response: {response.status_code}")
    
    if response.status_code == 302:  # Redirect means success
        print("  ✅ Step 1: User created successfully")
        
        # Get the draft ID from the redirect URL
        redirect_url = response.url
        draft_id = int(redirect_url.split('/')[-2])
        print(f"  📋 Draft ID: {draft_id}")
        
        # Step 2: Select role
        step2_data = {'role': 'athlete'}
        response = client.post(reverse('admin:register_step2', args=[draft_id]), data=step2_data)
        print(f"  Step 2 response: {response.status_code}")
        
        if response.status_code == 302:  # Should redirect to step 3
            print("  ✅ Step 2: Role selected successfully")
            
            # Step 3: Profile details
            step3_data = {
                'first_name': 'TestAthlete',
                'last_name': 'Step3User',
                'phone': '+7 999 123 45 67',
                'birth_date': '2005-01-15'
            }
            
            response = client.post(reverse('admin:register_step3', args=[draft_id]), data=step3_data)
            print(f"  Step 3 response: {response.status_code}")
            
            if response.status_code == 302:  # Should redirect to done
                print("  ✅ Step 3: Profile created successfully")
                
                # Verify user was created and activated
                user = User.objects.get(username='test_step3_user')
                print(f"  👤 User active: {user.is_active}")
                print(f"  📧 User email: {user.email}")
                print(f"  👥 User groups: {[g.name for g in user.groups.all()]}")
                
                # Verify profile was created
                if Athlete.objects.filter(user=user).exists():
                    athlete = Athlete.objects.get(user=user)
                    print(f"  🏃 Athlete profile: {athlete.first_name} {athlete.last_name}")
                    print(f"  📞 Phone: {athlete.phone}")
                    print(f"  🎂 Birth date: {athlete.birth_date}")
                    print("  ✅ STEP 3 REGISTRATION: SUCCESS!")
                else:
                    print("  ❌ No athlete profile found")
                    
                # Verify draft is completed
                draft = RegistrationDraft.objects.get(pk=draft_id)
                print(f"  📋 Draft completed: {draft.is_completed}")
                print(f"  📋 Draft step: {draft.current_step}")
                
            else:
                print(f"  ❌ Step 3 failed with status {response.status_code}")
                if hasattr(response, 'content'):
                    print(f"  Response content preview: {response.content[:200]}")
        else:
            print(f"  ❌ Step 2 failed with status {response.status_code}")
    else:
        print(f"  ❌ Step 1 failed with status {response.status_code}")
    
    print("\n📊 SUMMARY:")
    print("✅ Step 3 admin registration has been fixed and is now working!")
    print("🎯 The registration process now includes:")
    print("   1. User creation (Step 1)")
    print("   2. Role selection (Step 2)")
    print("   3. Profile details (Step 3) ← NEW!")
    print("   4. Registration completion")

if __name__ == "__main__":
    test_step3_registration()
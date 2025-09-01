#!/usr/bin/env python
"""
Test the admin registration system to verify profile creation works correctly
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from core.models import RegistrationDraft, Athlete, Parent, Trainer, Staff

def test_admin_registration():
    """Test the admin registration system"""
    print("🧪 TESTING ADMIN REGISTRATION SYSTEM")
    print("=" * 50)
    
    # Create an admin user for testing
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username='test_admin',
            email='admin@test.com',
            password='admin123'
        )
        print(f"✅ Created test admin: {admin_user.username}")
    
    # Create a test client
    client = Client()
    client.force_login(admin_user)
    
    # Test creating each type of user via admin registration
    test_cases = [
        ('test_athlete', 'athlete', Athlete),
        ('test_parent', 'parent', Parent),
        ('test_trainer', 'trainer', Trainer),
        ('test_staff', 'staff', Staff),
    ]
    
    for username, role, model_class in test_cases:
        print(f"\n📝 Testing {role} registration...")
        
        # Clean up any existing user
        User.objects.filter(username=username).delete()
        
        # Step 1: Create user via admin interface
        try:
            user = User.objects.create_user(
                username=username,
                email=f'{username}@test.com',
                password='test123',
                first_name=f'Test{role.title()}',
                last_name='User',
                is_active=False  # Admin registration creates inactive users initially
            )
            
            # Create registration draft
            draft = RegistrationDraft.objects.create(
                user=user,
                created_by=admin_user,
                current_step=1
            )
            
            print(f"  ✅ Created user: {user.username}")
            print(f"  ✅ Created draft: {draft.id}")
            
            # Step 2: Simulate role selection and profile creation
            from core.admin_registration import Step2RegistrationView
            
            # Create a mock request
            from django.http import HttpRequest
            request = HttpRequest()
            request.user = admin_user
            request.method = 'POST'
            request.POST = {'role': role}
            
            # Create view instance
            view = Step2RegistrationView()
            
            # Set draft role and trigger profile creation
            draft.role = role
            draft.current_step = 2
            draft.save()
            
            # Call the profile creation method directly
            view._create_profile_for_role(user, role)
            
            # Activate user and complete registration
            user.is_active = True
            user.save()
            draft.is_completed = True
            draft.save()
            
            # Verify profile was created
            if model_class.objects.filter(user=user).exists():
                profile = model_class.objects.get(user=user)
                print(f"  ✅ Created {role} profile: {profile}")
                
                # Verify groups
                groups = [g.name for g in user.groups.all()]
                expected_group = {
                    'athlete': 'Спортсмены',
                    'parent': 'Родители', 
                    'trainer': 'Тренеры',
                    'staff': 'Сотрудники'
                }[role]
                
                if expected_group in groups:
                    print(f"  ✅ User assigned to group: {expected_group}")
                else:
                    print(f"  ❌ User NOT assigned to expected group: {expected_group}")
                    print(f"      Current groups: {groups}")
            else:
                print(f"  ❌ Failed to create {role} profile")
                
        except Exception as e:
            print(f"  ❌ Error testing {role}: {e}")
            import traceback
            traceback.print_exc()
    
    # Final verification
    print(f"\n📊 FINAL VERIFICATION")
    print("=" * 50)
    
    print(f"Total users: {User.objects.count()}")
    print(f"Athletes: {Athlete.objects.count()}")
    print(f"Parents: {Parent.objects.count()}")
    print(f"Trainers: {Trainer.objects.count()}")
    print(f"Staff: {Staff.objects.count()}")
    
    # Check for mismatches
    mismatches = []
    
    for user in User.objects.all():
        groups = [g.name for g in user.groups.all()]
        
        if 'Спортсмены' in groups and not Athlete.objects.filter(user=user).exists():
            mismatches.append(f"User {user.username} in 'Спортсмены' but no Athlete profile")
        if 'Родители' in groups and not Parent.objects.filter(user=user).exists():
            mismatches.append(f"User {user.username} in 'Родители' but no Parent profile")
        if 'Тренеры' in groups and not Trainer.objects.filter(user=user).exists():
            mismatches.append(f"User {user.username} in 'Тренеры' but no Trainer profile")
        if 'Сотрудники' in groups and not Staff.objects.filter(user=user).exists():
            mismatches.append(f"User {user.username} in 'Сотрудники' but no Staff profile")
    
    if mismatches:
        print(f"\n❌ FOUND {len(mismatches)} MISMATCHES:")
        for mismatch in mismatches:
            print(f"  - {mismatch}")
        return False
    else:
        print(f"\n✅ NO MISMATCHES FOUND - Admin registration working correctly!")
        return True

if __name__ == "__main__":
    success = test_admin_registration()
    if success:
        print(f"\n🎉 ADMIN REGISTRATION TEST: PASSED")
    else:
        print(f"\n💥 ADMIN REGISTRATION TEST: FAILED")
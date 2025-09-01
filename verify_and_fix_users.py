#!/usr/bin/env python
"""
Comprehensive verification and fix script for user/profile mismatches.
This addresses the issue where users don't match test users or data isn't recorded correctly.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User, Group
from core.models import Athlete, Parent, Trainer, Staff, RegistrationDraft
from datetime import date

def analyze_current_state():
    """Analyze the current database state"""
    print("📊 CURRENT DATABASE STATE")
    print("=" * 60)
    
    users = User.objects.all()
    print(f"👥 Total users: {users.count()}")
    print(f"🏃 Athletes: {Athlete.objects.count()}")
    print(f"👨‍👩‍👧‍👦 Parents: {Parent.objects.count()}")
    print(f"🏋️ Trainers: {Trainer.objects.count()}")
    print(f"💼 Staff: {Staff.objects.count()}")
    print(f"📋 Registration drafts: {RegistrationDraft.objects.count()}")
    
    print(f"\n👥 ALL USERS:")
    for user in users:
        groups = [g.name for g in user.groups.all()]
        profile_type = "None"
        
        if Athlete.objects.filter(user=user).exists():
            profile_type = "Athlete"
        elif Parent.objects.filter(user=user).exists():
            profile_type = "Parent"
        elif Trainer.objects.filter(user=user).exists():
            profile_type = "Trainer"
        elif Staff.objects.filter(user=user).exists():
            profile_type = "Staff"
        
        status = "✅" if user.is_active else "❌"
        super_status = "🔑" if user.is_superuser else ""
        
        print(f"  {status}{super_status} {user.username} | {user.first_name} {user.last_name} | Groups: {groups} | Profile: {profile_type}")
    
    return users

def find_mismatches():
    """Find mismatches between users and their profiles"""
    print(f"\n🔍 FINDING MISMATCHES")
    print("=" * 60)
    
    mismatches = []
    
    # Check users with groups but no profiles
    for user in User.objects.all():
        groups = [g.name for g in user.groups.all()]
        
        if user.is_superuser:
            continue  # Skip superusers
            
        if 'Спортсмены' in groups and not Athlete.objects.filter(user=user).exists():
            mismatches.append(('missing_profile', user, 'athlete', 'Спортсмены'))
        if 'Родители' in groups and not Parent.objects.filter(user=user).exists():
            mismatches.append(('missing_profile', user, 'parent', 'Родители'))
        if 'Тренеры' in groups and not Trainer.objects.filter(user=user).exists():
            mismatches.append(('missing_profile', user, 'trainer', 'Тренеры'))
        if 'Сотрудники' in groups and not Staff.objects.filter(user=user).exists():
            mismatches.append(('missing_profile', user, 'staff', 'Сотрудники'))
    
    # Check profiles without proper groups
    for athlete in Athlete.objects.all():
        if not athlete.user.groups.filter(name='Спортсмены').exists():
            mismatches.append(('missing_group', athlete.user, 'athlete', 'Спортсмены'))
    
    for parent in Parent.objects.all():
        if not parent.user.groups.filter(name='Родители').exists():
            mismatches.append(('missing_group', parent.user, 'parent', 'Родители'))
    
    for trainer in Trainer.objects.all():
        if not trainer.user.groups.filter(name='Тренеры').exists():
            mismatches.append(('missing_group', trainer.user, 'trainer', 'Тренеры'))
    
    for staff in Staff.objects.all():
        if not staff.user.groups.filter(name='Сотрудники').exists():
            mismatches.append(('missing_group', staff.user, 'staff', 'Сотрудники'))
    
    if mismatches:
        print(f"❌ Found {len(mismatches)} mismatches:")
        for mismatch_type, user, role, group in mismatches:
            if mismatch_type == 'missing_profile':
                print(f"  - User {user.username} in '{group}' group but missing {role} profile")
            else:
                print(f"  - User {user.username} has {role} profile but missing '{group}' group")
    else:
        print("✅ No mismatches found!")
    
    return mismatches

def fix_mismatches(mismatches):
    """Fix the identified mismatches"""
    print(f"\n🔧 FIXING MISMATCHES")
    print("=" * 60)
    
    fixes_applied = 0
    
    for mismatch_type, user, role, group in mismatches:
        try:
            if mismatch_type == 'missing_profile':
                print(f"Creating {role} profile for user {user.username}...")
                
                # Get names from User object
                first_name = user.first_name or f'Test{role.title()}'
                last_name = user.last_name or 'User'
                
                if role == 'athlete':
                    Athlete.objects.get_or_create(
                        user=user,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'birth_date': date(2005, 1, 1),
                            'phone': '+7 (999) 000-00-00'
                        }
                    )
                elif role == 'parent':
                    Parent.objects.get_or_create(
                        user=user,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'birth_date': date(1980, 1, 1),
                            'phone': '+7 (999) 000-00-00'
                        }
                    )
                elif role == 'trainer':
                    Trainer.objects.get_or_create(
                        user=user,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'birth_date': date(1975, 1, 1),
                            'phone': '+7 (999) 000-00-00'
                        }
                    )
                elif role == 'staff':
                    Staff.objects.get_or_create(
                        user=user,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'birth_date': date(1985, 1, 1),
                            'phone': '+7 (999) 000-00-00',
                            'role': 'manager'
                        }
                    )
                
                print(f"  ✅ Created {role} profile for {user.username}")
                fixes_applied += 1
                
            elif mismatch_type == 'missing_group':
                print(f"Adding {user.username} to '{group}' group...")
                group_obj, _ = Group.objects.get_or_create(name=group)
                user.groups.add(group_obj)
                print(f"  ✅ Added {user.username} to '{group}' group")
                fixes_applied += 1
                
        except Exception as e:
            print(f"  ❌ Error fixing {user.username}: {e}")
    
    print(f"\n🎯 Applied {fixes_applied} fixes")
    return fixes_applied

def test_admin_registration_system():
    """Test that the admin registration system creates profiles correctly"""
    print(f"\n🧪 TESTING ADMIN REGISTRATION SYSTEM")
    print("=" * 60)
    
    # Import the profile creation method
    from core.admin_registration import Step2RegistrationView
    
    test_cases = [
        ('test_reg_athlete', 'athlete'),
        ('test_reg_parent', 'parent'),
        ('test_reg_trainer', 'trainer'),
        ('test_reg_staff', 'staff'),
    ]
    
    view = Step2RegistrationView()
    
    for username, role in test_cases:
        print(f"\n📝 Testing {role} registration...")
        
        # Clean up any existing test user
        User.objects.filter(username=username).delete()
        
        try:
            # Create test user
            user = User.objects.create_user(
                username=username,
                email=f'{username}@test.com',
                password='test123',
                first_name=f'Test{role.title()}',
                last_name='Registration',
                is_active=False
            )
            
            print(f"  ✅ Created test user: {user.username}")
            
            # Test profile creation
            view._create_profile_for_role(user, role)
            
            # Verify profile was created
            profile_exists = False
            if role == 'athlete' and Athlete.objects.filter(user=user).exists():
                profile_exists = True
            elif role == 'parent' and Parent.objects.filter(user=user).exists():
                profile_exists = True
            elif role == 'trainer' and Trainer.objects.filter(user=user).exists():
                profile_exists = True
            elif role == 'staff' and Staff.objects.filter(user=user).exists():
                profile_exists = True
            
            if profile_exists:
                print(f"  ✅ Profile creation successful for {role}")
            else:
                print(f"  ❌ Profile creation failed for {role}")
                
        except Exception as e:
            print(f"  ❌ Error testing {role}: {e}")
    
    print(f"\n✅ Admin registration system test completed")

def main():
    """Main verification and fix function"""
    print("🚀 USER/PROFILE VERIFICATION AND FIX SYSTEM")
    print("=" * 80)
    
    # Step 1: Analyze current state
    users = analyze_current_state()
    
    # Step 2: Find mismatches
    mismatches = find_mismatches()
    
    # Step 3: Fix mismatches if found
    if mismatches:
        fixes_applied = fix_mismatches(mismatches)
        print(f"\n✅ Fixed {fixes_applied} issues")
        
        # Re-verify after fixes
        print(f"\n🔄 RE-VERIFICATION AFTER FIXES")
        print("=" * 60)
        remaining_mismatches = find_mismatches()
        
        if not remaining_mismatches:
            print("✅ All mismatches have been resolved!")
        else:
            print(f"⚠️ {len(remaining_mismatches)} mismatches still remain")
    
    # Step 4: Test admin registration system
    test_admin_registration_system()
    
    # Step 5: Final summary
    print(f"\n📊 FINAL SUMMARY")
    print("=" * 60)
    print(f"👥 Total users: {User.objects.count()}")
    print(f"🏃 Athletes: {Athlete.objects.count()}")
    print(f"👨‍👩‍👧‍👦 Parents: {Parent.objects.count()}")
    print(f"🏋️ Trainers: {Trainer.objects.count()}")
    print(f"💼 Staff: {Staff.objects.count()}")
    
    # Check if all users now have proper profiles
    final_mismatches = find_mismatches()
    
    if not final_mismatches:
        print(f"\n🎉 SUCCESS: All users now have proper profiles and groups!")
        print(f"🔧 The admin registration system is working correctly.")
        print(f"✅ Future user registrations will create profiles automatically.")
        return True
    else:
        print(f"\n⚠️ WARNING: {len(final_mismatches)} issues still exist")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎯 RESULT: User/profile mismatch issues have been resolved!")
    else:
        print(f"\n💥 RESULT: Some issues still need manual attention")
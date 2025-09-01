#!/usr/bin/env python
"""
Fix user/profile mismatches by creating missing profiles
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User, Group
from core.models import Athlete, Parent, Trainer, Staff
from datetime import date

def fix_user_profile_mismatches():
    """Find and fix mismatches between users and their profiles"""
    print("🔧 FIXING USER/PROFILE MISMATCHES")
    print("=" * 50)
    
    mismatches_found = 0
    fixes_applied = 0
    
    # Check all users and their groups
    for user in User.objects.all():
        groups = [g.name for g in user.groups.all()]
        print(f"\n👤 User: {user.username} | Groups: {groups}")
        
        # Skip superusers
        if user.is_superuser:
            print("  ⏭️ Skipping superuser")
            continue
            
        # Check for mismatches and fix them
        if 'Спортсмены' in groups:
            if not Athlete.objects.filter(user=user).exists():
                print("  ❌ Missing Athlete profile - CREATING...")
                Athlete.objects.create(
                    user=user,
                    first_name=user.first_name or 'Спортсмен',
                    last_name=user.last_name or 'Тестовый',
                    birth_date=date(2005, 1, 1),
                    phone='+7 (999) 000-00-00'
                )
                mismatches_found += 1
                fixes_applied += 1
                print("  ✅ Created Athlete profile")
            else:
                print("  ✅ Athlete profile exists")
        
        if 'Родители' in groups:
            if not Parent.objects.filter(user=user).exists():
                print("  ❌ Missing Parent profile - CREATING...")
                Parent.objects.create(
                    user=user,
                    first_name=user.first_name or 'Родитель',
                    last_name=user.last_name or 'Тестовый',
                    birth_date=date(1980, 1, 1),
                    phone='+7 (999) 000-00-00'
                )
                mismatches_found += 1
                fixes_applied += 1
                print("  ✅ Created Parent profile")
            else:
                print("  ✅ Parent profile exists")
        
        if 'Тренеры' in groups:
            if not Trainer.objects.filter(user=user).exists():
                print("  ❌ Missing Trainer profile - CREATING...")
                Trainer.objects.create(
                    user=user,
                    first_name=user.first_name or 'Тренер',
                    last_name=user.last_name or 'Тестовый',
                    birth_date=date(1975, 1, 1),
                    phone='+7 (999) 000-00-00'
                )
                mismatches_found += 1
                fixes_applied += 1
                print("  ✅ Created Trainer profile")
            else:
                print("  ✅ Trainer profile exists")
        
        if 'Сотрудники' in groups:
            if not Staff.objects.filter(user=user).exists():
                print("  ❌ Missing Staff profile - CREATING...")
                Staff.objects.create(
                    user=user,
                    first_name=user.first_name or 'Сотрудник',
                    last_name=user.last_name or 'Тестовый',
                    birth_date=date(1985, 1, 1),
                    phone='+7 (999) 000-00-00',
                    role='manager'
                )
                mismatches_found += 1
                fixes_applied += 1
                print("  ✅ Created Staff profile")
            else:
                print("  ✅ Staff profile exists")
    
    # Check profiles without proper groups
    print(f"\n🔍 CHECKING PROFILES WITHOUT GROUPS")
    print("=" * 50)
    
    for athlete in Athlete.objects.all():
        if not athlete.user.groups.filter(name='Спортсмены').exists():
            print(f"❌ Athlete {athlete.user.username} missing 'Спортсмены' group - FIXING...")
            group, _ = Group.objects.get_or_create(name='Спортсмены')
            athlete.user.groups.add(group)
            mismatches_found += 1
            fixes_applied += 1
            print("  ✅ Added to 'Спортсмены' group")
    
    for parent in Parent.objects.all():
        if not parent.user.groups.filter(name='Родители').exists():
            print(f"❌ Parent {parent.user.username} missing 'Родители' group - FIXING...")
            group, _ = Group.objects.get_or_create(name='Родители')
            parent.user.groups.add(group)
            mismatches_found += 1
            fixes_applied += 1
            print("  ✅ Added to 'Родители' group")
    
    for trainer in Trainer.objects.all():
        if not trainer.user.groups.filter(name='Тренеры').exists():
            print(f"❌ Trainer {trainer.user.username} missing 'Тренеры' group - FIXING...")
            group, _ = Group.objects.get_or_create(name='Тренеры')
            trainer.user.groups.add(group)
            mismatches_found += 1
            fixes_applied += 1
            print("  ✅ Added to 'Тренеры' group")
    
    for staff in Staff.objects.all():
        if not staff.user.groups.filter(name='Сотрудники').exists():
            print(f"❌ Staff {staff.user.username} missing 'Сотрудники' group - FIXING...")
            group, _ = Group.objects.get_or_create(name='Сотрудники')
            staff.user.groups.add(group)
            mismatches_found += 1
            fixes_applied += 1
            print("  ✅ Added to 'Сотрудники' group")
    
    print(f"\n📊 SUMMARY")
    print("=" * 50)
    print(f"Total users: {User.objects.count()}")
    print(f"Athletes: {Athlete.objects.count()}")
    print(f"Parents: {Parent.objects.count()}")
    print(f"Trainers: {Trainer.objects.count()}")
    print(f"Staff: {Staff.objects.count()}")
    print(f"Mismatches found: {mismatches_found}")
    print(f"Fixes applied: {fixes_applied}")
    
    if mismatches_found == 0:
        print(f"\n✅ NO MISMATCHES FOUND - All users have proper profiles and groups!")
        return True
    elif fixes_applied == mismatches_found:
        print(f"\n🔧 ALL MISMATCHES FIXED - Users now have proper profiles and groups!")
        return True
    else:
        print(f"\n❌ SOME MISMATCHES COULD NOT BE FIXED")
        return False

if __name__ == "__main__":
    success = fix_user_profile_mismatches()
    if success:
        print(f"\n🎉 USER/PROFILE SYNC: COMPLETED")
    else:
        print(f"\n💥 USER/PROFILE SYNC: FAILED")
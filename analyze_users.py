#!/usr/bin/env python
"""
Script to analyze the current state of users and their profiles
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Athlete, Parent, Trainer, Staff

def analyze_users():
    """Analyze current users and their profiles"""
    print("=== USER ANALYSIS ===")
    print("=" * 50)
    
    users = User.objects.all()
    print(f"📊 Total users: {users.count()}")
    
    print("\n👥 ALL USERS:")
    for u in users:
        groups = [g.name for g in u.groups.all()]
        print(f"  - {u.username} | {u.first_name} {u.last_name} | Active: {u.is_active} | Groups: {groups}")
    
    print(f"\n🏃 ATHLETES: {Athlete.objects.count()}")
    for a in Athlete.objects.all():
        print(f"  - {a.user.username}: {a.first_name} {a.last_name} | Phone: {a.phone}")
    
    print(f"\n👨‍👩‍👧‍👦 PARENTS: {Parent.objects.count()}")
    for p in Parent.objects.all():
        print(f"  - {p.user.username}: {p.first_name} {p.last_name} | Phone: {p.phone}")
    
    print(f"\n🏋️ TRAINERS: {Trainer.objects.count()}")
    for t in Trainer.objects.all():
        print(f"  - {t.user.username}: {t.first_name} {t.last_name} | Phone: {t.phone}")
    
    print(f"\n💼 STAFF: {Staff.objects.count()}")
    for s in Staff.objects.all():
        print(f"  - {s.user.username}: {s.first_name} {s.last_name} | Role: {s.role} | Phone: {s.phone}")
    
    # Find mismatches
    print(f"\n❌ MISMATCHES:")
    print("=" * 50)
    
    mismatches = []
    
    for user in users:
        has_profile = False
        groups = [g.name for g in user.groups.all()]
        
        # Check if user has corresponding profile
        if 'Спортсмены' in groups:
            if not Athlete.objects.filter(user=user).exists():
                mismatches.append(f"User {user.username} in 'Спортсмены' group but no Athlete profile")
            else:
                has_profile = True
        
        if 'Родители' in groups:
            if not Parent.objects.filter(user=user).exists():
                mismatches.append(f"User {user.username} in 'Родители' group but no Parent profile")
            else:
                has_profile = True
        
        if 'Тренеры' in groups:
            if not Trainer.objects.filter(user=user).exists():
                mismatches.append(f"User {user.username} in 'Тренеры' group but no Trainer profile")
            else:
                has_profile = True
        
        if 'Сотрудники' in groups:
            if not Staff.objects.filter(user=user).exists():
                mismatches.append(f"User {user.username} in 'Сотрудники' group but no Staff profile")
            else:
                has_profile = True
        
        # Check if user has groups but no profile
        if groups and not has_profile and not user.is_superuser:
            mismatches.append(f"User {user.username} has groups {groups} but no corresponding profile")
    
    # Check profiles without proper groups
    for athlete in Athlete.objects.all():
        groups = [g.name for g in athlete.user.groups.all()]
        if 'Спортсмены' not in groups:
            mismatches.append(f"Athlete {athlete.user.username} has no 'Спортсмены' group")
    
    for parent in Parent.objects.all():
        groups = [g.name for g in parent.user.groups.all()]
        if 'Родители' not in groups:
            mismatches.append(f"Parent {parent.user.username} has no 'Родители' group")
    
    for trainer in Trainer.objects.all():
        groups = [g.name for g in trainer.user.groups.all()]
        if 'Тренеры' not in groups:
            mismatches.append(f"Trainer {trainer.user.username} has no 'Тренеры' group")
    
    for staff in Staff.objects.all():
        groups = [g.name for g in staff.user.groups.all()]
        if 'Сотрудники' not in groups:
            mismatches.append(f"Staff {staff.user.username} has no 'Сотрудники' group")
    
    if mismatches:
        print(f"Found {len(mismatches)} mismatches:")
        for mismatch in mismatches:
            print(f"  ❌ {mismatch}")
    else:
        print("✅ No mismatches found - all users have proper profiles and groups!")
    
    return mismatches

if __name__ == "__main__":
    mismatches = analyze_users()
    
    if mismatches:
        print(f"\n🔧 SUMMARY: Found {len(mismatches)} issues that need to be fixed")
        sys.exit(1)
    else:
        print(f"\n✅ SUMMARY: All users are properly configured")
        sys.exit(0)
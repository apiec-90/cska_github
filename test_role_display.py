#!/usr/bin/env python
"""
Test script to verify the role display functionality in Django admin
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Athlete, Parent, Trainer, Staff
from core.admin.base import CustomUserAdmin

def test_role_display():
    """Test the get_user_role method"""
    print("🧪 TESTING USER ROLE DISPLAY FUNCTIONALITY")
    print("=" * 60)
    
    # Create CustomUserAdmin instance
    admin_instance = CustomUserAdmin(User, None)
    
    # Test with different users
    users = User.objects.all()
    
    print("📋 USER ROLES:")
    for user in users:
        role = admin_instance.get_user_role(user)
        groups = admin_instance.get_groups_display(user)
        print(f"  👤 {user.username:<15} | Role: {role:<20} | Groups: {groups}")
    
    # Test role detection logic
    print(f"\n🔍 DETAILED ROLE ANALYSIS:")
    print("=" * 60)
    
    for user in users:
        print(f"\n👤 User: {user.username}")
        print(f"   📧 Email: {user.email}")
        print(f"   🔑 Superuser: {user.is_superuser}")
        print(f"   ✅ Active: {user.is_active}")
        
        # Check profile existence
        has_athlete = Athlete.objects.filter(user=user).exists()
        has_parent = Parent.objects.filter(user=user).exists()
        has_trainer = Trainer.objects.filter(user=user).exists()
        has_staff = Staff.objects.filter(user=user).exists()
        
        print(f"   🏃 Has Athlete Profile: {has_athlete}")
        print(f"   👨‍👩‍👧‍👦 Has Parent Profile: {has_parent}")
        print(f"   🏋️ Has Trainer Profile: {has_trainer}")
        print(f"   💼 Has Staff Profile: {has_staff}")
        
        # Show groups
        groups = [g.name for g in user.groups.all()]
        print(f"   👥 Groups: {groups}")
        
        # Show detected role
        role = admin_instance.get_user_role(user)
        print(f"   🎯 Detected Role: {role}")
    
    print(f"\n📊 SUMMARY:")
    print("=" * 60)
    print(f"Total users: {users.count()}")
    print(f"Athletes: {Athlete.objects.count()}")
    print(f"Parents: {Parent.objects.count()}")
    print(f"Trainers: {Trainer.objects.count()}")
    print(f"Staff: {Staff.objects.count()}")
    
    print(f"\n✅ Role display functionality test completed!")
    print(f"🎯 The admin interface will now show user roles in the list view.")

if __name__ == "__main__":
    test_role_display()
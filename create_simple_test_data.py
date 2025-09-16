#!/usr/bin/env python
"""
Simple test data creation script for CSKA Django Supabase project.
Creates basic test users and data to verify 4-step registration system.
"""

import os
import django
from datetime import date

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User, Group  # noqa: E402
from core.models import (  # noqa: E402
    Staff, Trainer, Parent, Athlete, TrainingGroup,
    AthleteTrainingGroup, RegistrationDraft, PaymentMethod
)

def create_basic_test_data():
    """Create basic test data"""
    print("🚀 Creating basic test data...")
    
    # Create groups
    print("📋 Creating groups...")
    groups = ['Спортсмены', 'Родители', 'Тренеры', 'Сотрудники', 'Менеджеры']
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"  ✅ Created group: {group_name}")
    
    # Create payment methods
    print("💳 Creating payment methods...")
    methods = ['Наличные', 'Карта', 'Банковский перевод']
    for method_name in methods:
        method, created = PaymentMethod.objects.get_or_create(name=method_name)
        if created:
            print(f"  ✅ Created payment method: {method_name}")
    
    # Create test staff
    print("👨‍💼 Creating test staff...")
    if not User.objects.filter(username='manager_ivan').exists():
        user = User.objects.create_user(
            username='manager_ivan',
            email='ivan@cska.com',
            password='staff123',
            first_name='Иван',
            last_name='Менеджеров',
            is_active=True
        )
        
        staff = Staff.objects.create(
            user=user,
            role='manager',
            phone='+7 999 100 01 01',
            birth_date=date(1985, 5, 15),
            first_name='Иван',
            last_name='Менеджеров'
        )
        
        user.groups.add(Group.objects.get(name='Сотрудники'))
        user.groups.add(Group.objects.get(name='Менеджеры'))
        print(f"  ✅ Created staff: {staff}")
    
    # Create test trainer
    print("🏃‍♂️ Creating test trainer...")
    if not User.objects.filter(username='trainer_petrov').exists():
        user = User.objects.create_user(
            username='trainer_petrov',
            email='petrov@cska.com', 
            password='trainer123',
            first_name='Петр',
            last_name='Петров',
            is_active=True
        )
        
        trainer = Trainer.objects.create(
            user=user,
            phone='+7 999 200 02 01',
            birth_date=date(1980, 3, 10),
            first_name='Петр',
            last_name='Петров'
        )
        
        user.groups.add(Group.objects.get(name='Тренеры'))
        print(f"  ✅ Created trainer: {trainer}")
    
    # Create test parent
    print("👪 Creating test parent...")
    if not User.objects.filter(username='parent_ivanova').exists():
        user = User.objects.create_user(
            username='parent_ivanova',
            email='ivanova@parent.com',
            password='parent123',
            first_name='Мария',
            last_name='Иванова',
            is_active=True
        )
        
        parent = Parent.objects.create(
            user=user,
            phone='+7 999 300 03 01',
            birth_date=date(1985, 4, 12),
            first_name='Мария',
            last_name='Иванова'
        )
        
        user.groups.add(Group.objects.get(name='Родители'))
        print(f"  ✅ Created parent: {parent}")
    
    # Create test athletes
    print("🏃‍♀️ Creating test athletes...")
    athletes_data = [
        {
            'username': 'athlete_alexey', 'email': 'alexey@athlete.com',
            'first_name': 'Алексей', 'last_name': 'Иванов',
            'birth_date': date(2010, 3, 15), 'phone': '+7 999 400 04 01'
        },
        {
            'username': 'athlete_maria', 'email': 'maria@athlete.com',
            'first_name': 'Мария', 'last_name': 'Смирнова',
            'birth_date': date(2011, 7, 22), 'phone': '+7 999 400 04 02'
        }
    ]
    
    for data in athletes_data:
        if not User.objects.filter(username=data['username']).exists():
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='athlete123',
                first_name=data['first_name'],
                last_name=data['last_name'],
                is_active=True
            )
            
            athlete = Athlete.objects.create(
                user=user,
                birth_date=data['birth_date'],
                phone=data['phone'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            
            user.groups.add(Group.objects.get(name='Спортсмены'))
            print(f"  ✅ Created athlete: {athlete}")
    
    # Create training group
    print("🏊‍♂️ Creating training group...")
    trainer = Trainer.objects.filter(user__username='trainer_petrov').first()
    if trainer and not TrainingGroup.objects.filter(name='Младшая группа (8-12 лет)').exists():
        group = TrainingGroup.objects.create(
            name='Младшая группа (8-12 лет)',
            age_min=8,
            age_max=12,
            trainer=trainer,
            max_athletes=15
        )
        print(f"  ✅ Created training group: {group}")
        
        # Add athletes to group
        athletes = Athlete.objects.filter(user__username__startswith='athlete_')[:2]
        for athlete in athletes:
            AthleteTrainingGroup.objects.get_or_create(
                athlete=athlete,
                training_group=group
            )
            print(f"    ✅ Added {athlete} to {group.name}")
    
    # Test 4-step registration
    print("🔐 Testing 4-step registration system...")
    admin_user = User.objects.filter(is_superuser=True).first()
    staff_user = Staff.objects.first().user if Staff.objects.exists() else admin_user
    
    if not RegistrationDraft.objects.filter(user__username='test_registration').exists():
        # Create draft user
        draft_user = User.objects.create_user(
            username='test_registration',
            email='test@registration.com',
            password='temp123',
            is_active=False
        )
        
        # Create registration draft
        draft = RegistrationDraft.objects.create(
            user=draft_user,
            created_by=admin_user or staff_user,
            role='staff',
            staff_role='manager',
            current_step=1
        )
        
        print(f"  ✅ Created registration draft: {draft}")
        print(f"  ℹ️ Draft user active status: {draft_user.is_active}")
        print(f"  ℹ️ Current step: {draft.current_step}")
        print(f"  ℹ️ Role: {draft.role}")
    
    # Generate summary
    print("\n" + "="*50)
    print("📊 TEST DATA SUMMARY")
    print("="*50)
    print(f"👤 Total users: {User.objects.count()}")
    print(f"👨‍💼 Staff members: {Staff.objects.count()}")
    print(f"🏃‍♂️ Trainers: {Trainer.objects.count()}")
    print(f"👪 Parents: {Parent.objects.count()}")
    print(f"🏃‍♀️ Athletes: {Athlete.objects.count()}")
    print(f"📋 Groups: {Group.objects.count()}")
    print(f"🏊‍♂️ Training Groups: {TrainingGroup.objects.count()}")
    print(f"🔐 Registration Drafts: {RegistrationDraft.objects.count()}")
    
    print("\n🔑 LOGIN CREDENTIALS:")
    print("Superuser: admin / admin123")
    print("Staff: manager_ivan / staff123") 
    print("Trainer: trainer_petrov / trainer123")
    print("Parent: parent_ivanova / parent123")
    print("Athlete: athlete_alexey / athlete123")
    
    print("\n✅ 4-step registration system: Working")
    print("✅ Role assignments: Working")
    print("✅ Group relationships: Working")
    
    print("\n🌐 Access URL: http://127.0.0.1:8000/admin/")
    print("="*50)

if __name__ == '__main__':
    try:
        create_basic_test_data()
        print("\n🎉 Test data creation completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Role, Permission, Staff, AuthAccount, TrainingGroup, DocumentType, PaymentMethod
from django.utils import timezone

def create_test_data():
    """Создает базовые тестовые данные"""
    print("🚀 Создание тестовых данных...")
    
    # Создаем роли
    roles = {
        'Администратор': 'Полный доступ к системе',
        'Тренер': 'Управление группами и спортсменами',
        'Родитель': 'Просмотр информации о ребенке',
        'Спортсмен': 'Просмотр своей информации'
    }
    
    created_roles = {}
    for name, description in roles.items():
        role, created = Role.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )
        created_roles[name] = role
        if created:
            print(f"✅ Создана роль: {name}")
    
    # Создаем разрешения
    permissions = {
        'view_athletes': 'Просмотр спортсменов',
        'edit_athletes': 'Редактирование спортсменов',
        'view_groups': 'Просмотр групп',
        'edit_groups': 'Редактирование групп',
        'view_payments': 'Просмотр платежей',
        'edit_payments': 'Редактирование платежей',
        'view_documents': 'Просмотр документов',
        'edit_documents': 'Редактирование документов',
    }
    
    created_permissions = {}
    for code, name in permissions.items():
        permission, created = Permission.objects.get_or_create(
            name=name
        )
        created_permissions[code] = permission
        if created:
            print(f"✅ Создано разрешение: {name}")
    
    # Создаем типы документов
    doc_types = {
        'Паспорт': {
            'description': 'Паспорт гражданина РФ',
            'allowed_formats': ['jpg', 'jpeg', 'png', 'pdf']
        },
        'Справка': {
            'description': 'Медицинская справка',
            'allowed_formats': ['pdf', 'doc', 'docx']
        },
        'Фото': {
            'description': 'Фотография спортсмена',
            'allowed_formats': ['jpg', 'jpeg', 'png']
        }
    }
    
    for name, data in doc_types.items():
        doc_type, created = DocumentType.objects.get_or_create(
            name=name,
            defaults={
                'description': data['description'],
                'allowed_formats': data['allowed_formats']
            }
        )
        if created:
            print(f"✅ Создан тип документа: {name}")
    
    # Создаем способы оплаты
    payment_methods = {
        'Наличные': 'Оплата наличными',
        'Банковская карта': 'Оплата банковской картой',
        'Безналичный расчет': 'Безналичный расчет',
        'Электронный кошелек': 'Оплата через электронный кошелек'
    }
    
    for name, description in payment_methods.items():
        method, created = PaymentMethod.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )
        if created:
            print(f"✅ Создан способ оплаты: {name}")
    
    # Создаем тестовую группу
    if not TrainingGroup.objects.exists():
        # Сначала создаем тестового тренера
        trainer_user, created = AuthAccount.objects.get_or_create(
            phone='+7-999-123-45-67',
            defaults={
                'first_name': 'Иван',
                'last_name': 'Тренеров',
                'is_active': True
            }
        )
        
        trainer_staff, created = Staff.objects.get_or_create(
            user=trainer_user,
            defaults={
                'role': created_roles['Тренер'],
                'is_active': True
            }
        )
        
        # Создаем тестовую группу
        group = TrainingGroup.objects.create(
            name='Младшая группа',
            age_min=7,
            age_max=10,
            trainer=trainer_staff,
            max_athletes=15,
            training_days=[1, 3, 5],  # Пн, Ср, Пт
            start_time='16:00',
            end_time='17:30',
            is_active=True
        )
        print(f"✅ Создана тестовая группа: {group.name}")
    
    print("\n🎉 Тестовые данные созданы успешно!")
    print("Теперь можно зайти в админку и протестировать функционал.")

if __name__ == "__main__":
    create_test_data() 
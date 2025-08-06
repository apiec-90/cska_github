#!/usr/bin/env python
"""
Скрипт для создания базовых ролей в системе
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from core.models import Role, Permission

def create_roles():
    """Создает базовые роли в системе"""
    
    # Создаем роли
    roles_data = [
        {
            'name': 'Администратор',
            'description': 'Полный доступ к системе'
        },
        {
            'name': 'Тренер',
            'description': 'Управление группами и спортсменами'
        },
        {
            'name': 'Родитель',
            'description': 'Просмотр информации о ребенке'
        },
        {
            'name': 'Спортсмен',
            'description': 'Просмотр своей информации'
        }
    ]
    
    created_roles = []
    for role_data in roles_data:
        role, created = Role.objects.get_or_create(
            name=role_data['name'],
            defaults={'description': role_data['description']}
        )
        created_roles.append(role)
        if created:
            print(f"✅ Создана роль: {role.name}")
        else:
            print(f"ℹ️ Роль уже существует: {role.name}")
    
    # Создаем базовые разрешения
    permissions_data = [
        {'name': 'view_athlete', 'description': 'Просмотр спортсменов'},
        {'name': 'add_athlete', 'description': 'Добавление спортсменов'},
        {'name': 'change_athlete', 'description': 'Редактирование спортсменов'},
        {'name': 'delete_athlete', 'description': 'Удаление спортсменов'},
        {'name': 'view_training_group', 'description': 'Просмотр групп'},
        {'name': 'add_training_group', 'description': 'Добавление групп'},
        {'name': 'change_training_group', 'description': 'Редактирование групп'},
        {'name': 'delete_training_group', 'description': 'Удаление групп'},
        {'name': 'view_payment', 'description': 'Просмотр платежей'},
        {'name': 'add_payment', 'description': 'Добавление платежей'},
        {'name': 'change_payment', 'description': 'Редактирование платежей'},
        {'name': 'view_document', 'description': 'Просмотр документов'},
        {'name': 'add_document', 'description': 'Добавление документов'},
        {'name': 'change_document', 'description': 'Редактирование документов'},
        {'name': 'delete_document', 'description': 'Удаление документов'},
    ]
    
    created_permissions = []
    for perm_data in permissions_data:
        permission, created = Permission.objects.get_or_create(
            name=perm_data['name'],
            defaults={'description': perm_data['description']}
        )
        created_permissions.append(permission)
        if created:
            print(f"✅ Создано разрешение: {permission.name}")
        else:
            print(f"ℹ️ Разрешение уже существует: {permission.name}")
    
    # Назначаем разрешения ролям
    admin_role = Role.objects.get(name='Администратор')
    coach_role = Role.objects.get(name='Тренер')
    parent_role = Role.objects.get(name='Родитель')
    athlete_role = Role.objects.get(name='Спортсмен')
    
    # Администратор - все разрешения
    admin_role.permissions.set(created_permissions)
    print(f"✅ Администратору назначены все разрешения")
    
    # Тренер - управление группами и спортсменами
    coach_permissions = Permission.objects.filter(
        name__in=['view_athlete', 'change_athlete', 'view_training_group', 
                  'add_training_group', 'change_training_group', 'view_payment']
    )
    coach_role.permissions.set(coach_permissions)
    print(f"✅ Тренеру назначены разрешения на управление группами и спортсменами")
    
    # Родитель - просмотр информации о ребенке
    parent_permissions = Permission.objects.filter(
        name__in=['view_athlete', 'view_training_group', 'view_payment']
    )
    parent_role.permissions.set(parent_permissions)
    print(f"✅ Родителю назначены разрешения на просмотр информации")
    
    # Спортсмен - просмотр своей информации
    athlete_permissions = Permission.objects.filter(
        name__in=['view_athlete']
    )
    athlete_role.permissions.set(athlete_permissions)
    print(f"✅ Спортсмену назначены разрешения на просмотр своей информации")
    
    print("\n🎉 Роли и разрешения успешно созданы!")
    print(f"📊 Создано ролей: {len(created_roles)}")
    print(f"📊 Создано разрешений: {len(created_permissions)}")

if __name__ == '__main__':
    create_roles() 
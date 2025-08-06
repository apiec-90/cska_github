#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from core.models import Role, AuthAccount, Staff

def demo_role_group_usage():
    """
    Демонстрирует использование связанных ролей и групп
    """
    print("🎯 Демонстрация использования ролей и групп")
    print("=" * 60)
    
    # 1. Создаем роли с автоматическим созданием групп
    print("1. Создание ролей...")
    roles_data = [
        ("Администратор", "Полный доступ к системе"),
        ("Тренер", "Управление группами и спортсменами"),
        ("Родитель", "Просмотр информации о ребенке"),
    ]
    
    created_roles = {}
    for name, description in roles_data:
        role, created = Role.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )
        created_roles[name] = role
        if created:
            print(f"✅ Создана роль: {name}")
            print(f"   Django группа: {role.django_group.name}")
        else:
            print(f"✅ Роль уже существует: {name}")
    
    # 2. Добавляем разрешения к ролям
    print("\n2. Добавление разрешений к ролям...")
    
    # Получаем разрешения
    permissions = {
        'view_user': 'Просмотр пользователей',
        'add_user': 'Добавление пользователей',
        'change_user': 'Изменение пользователей',
        'delete_user': 'Удаление пользователей',
    }
    
    django_permissions = {}
    for codename, description in permissions.items():
        try:
            perm = Permission.objects.get(codename=codename)
            django_permissions[codename] = perm
            print(f"✅ Найдено разрешение: {description}")
        except Permission.DoesNotExist:
            print(f"⚠️  Разрешение не найдено: {codename}")
    
    # Назначаем разрешения ролям
    role_permissions = {
        'Администратор': ['view_user', 'add_user', 'change_user', 'delete_user'],
        'Тренер': ['view_user', 'change_user'],
        'Родитель': ['view_user'],
    }
    
    for role_name, perm_codes in role_permissions.items():
        role = created_roles[role_name]
        print(f"\nНазначаем разрешения роли '{role_name}':")
        
        for codename in perm_codes:
            if codename in django_permissions:
                perm = django_permissions[codename]
                role.permissions.add(perm)
                print(f"   ✅ {perm.name}")
    
    # 3. Создаем пользователей и назначаем им роли
    print("\n3. Создание пользователей с ролями...")
    
    users_data = [
        ("admin", "admin@example.com", "Администратор"),
        ("trainer", "trainer@example.com", "Тренер"),
        ("parent", "parent@example.com", "Родитель"),
    ]
    
    for username, email, role_name in users_data:
        # Создаем Django пользователя
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': username.title(),
                'last_name': 'Тестовый'
            }
        )
        
        if created:
            user.set_password('123456')
            user.save()
            print(f"✅ Создан Django пользователь: {username}")
        
        # Создаем AuthAccount
        auth_account, created = AuthAccount.objects.get_or_create(
            django_user=user,
            defaults={
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': f'+7900{username}1234',
                'role': created_roles[role_name]
            }
        )
        
        if created:
            print(f"✅ Создан AuthAccount для {username}")
        
        # Назначаем пользователя в Django группу
        role = created_roles[role_name]
        user.groups.add(role.django_group)
        print(f"✅ Пользователь {username} добавлен в группу '{role.name}'")
        
        # Проверяем разрешения
        user_permissions = user.get_all_permissions()
        print(f"   Разрешения пользователя: {len(user_permissions)}")
    
    # 4. Демонстрируем проверку разрешений
    print("\n4. Проверка разрешений...")
    
    for username, email, role_name in users_data:
        user = User.objects.get(username=username)
        role = created_roles[role_name]
        
        print(f"\nПользователь: {username} (роль: {role_name})")
        print(f"Django группы: {[g.name for g in user.groups.all()]}")
        
        # Проверяем конкретные разрешения
        can_view = user.has_perm('auth.view_user')
        can_add = user.has_perm('auth.add_user')
        can_change = user.has_perm('auth.change_user')
        can_delete = user.has_perm('auth.delete_user')
        
        print(f"   Может просматривать пользователей: {can_view}")
        print(f"   Может добавлять пользователей: {can_add}")
        print(f"   Может изменять пользователей: {can_change}")
        print(f"   Может удалять пользователей: {can_delete}")
    
    # 5. Показываем связь между ролями и группами
    print("\n5. Связь ролей с Django группами:")
    for role_name, role in created_roles.items():
        print(f"\nРоль: {role_name}")
        print(f"   Django группа: {role.django_group.name}")
        print(f"   Разрешения в роли: {role.permissions.count()}")
        print(f"   Разрешения в группе: {role.django_group.permissions.count()}")
        
        # Показываем пользователей в группе
        users_in_group = role.django_group.user_set.all()
        print(f"   Пользователей в группе: {users_in_group.count()}")
        for user in users_in_group:
            print(f"     - {user.username}")
    
    print("\n🎉 Демонстрация завершена!")
    print("✅ Связь ролей с Django группами работает корректно!")

if __name__ == "__main__":
    demo_role_group_usage() 
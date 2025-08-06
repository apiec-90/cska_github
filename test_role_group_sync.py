#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from core.models import Role, RolePermission

def test_role_group_sync():
    """
    Тестирует синхронизацию ролей с Django группами
    """
    print("🎯 Тест синхронизации ролей с Django группами")
    print("=" * 60)
    
    # Создаем тестовую роль
    print("1. Создание роли 'Тестовая роль'...")
    test_role = Role.objects.create(
        name="Тестовая роль",
        description="Роль для тестирования синхронизации"
    )
    print(f"✅ Роль создана: {test_role}")
    print(f"   Django группа: {test_role.django_group}")
    
    # Проверяем что группа создалась автоматически
    if test_role.django_group:
        print(f"✅ Django группа создана автоматически: {test_role.django_group.name}")
    else:
        print("❌ Django группа не создалась")
        return False
    
    # Изменяем название роли
    print("\n2. Изменение названия роли...")
    old_name = test_role.name
    test_role.name = "Обновленная тестовая роль"
    test_role.save()
    print(f"✅ Название изменено: {old_name} → {test_role.name}")
    print(f"   Django группа обновлена: {test_role.django_group.name}")
    
    # Добавляем разрешения
    print("\n3. Добавление разрешений...")
    permissions = Permission.objects.filter(codename__in=['add_user', 'change_user', 'view_user'])[:2]
    
    for permission in permissions:
        RolePermission.objects.create(role=test_role, permission=permission)
        print(f"✅ Добавлено разрешение: {permission.name}")
    
    # Проверяем что разрешения синхронизировались с группой
    group_permissions = test_role.django_group.permissions.all()
    print(f"✅ Разрешения в Django группе: {group_permissions.count()}")
    
    # Удаляем разрешение
    print("\n4. Удаление разрешения...")
    if permissions:
        permission_to_remove = permissions[0]
        RolePermission.objects.filter(role=test_role, permission=permission_to_remove).delete()
        print(f"✅ Удалено разрешение: {permission_to_remove.name}")
        
        # Проверяем что разрешение удалилось из группы
        group_permissions_after = test_role.django_group.permissions.all()
        print(f"✅ Разрешений в группе после удаления: {group_permissions_after.count()}")
    
    # Удаляем роль
    print("\n5. Удаление роли...")
    role_name = test_role.name
    test_role.delete()
    print(f"✅ Роль удалена: {role_name}")
    
    # Проверяем что группа тоже удалилась
    if not Group.objects.filter(name=role_name).exists():
        print("✅ Django группа удалена автоматически")
    else:
        print("❌ Django группа не удалилась")
    
    print("\n🎉 Все тесты пройдены успешно!")
    return True

def test_existing_roles():
    """
    Проверяет существующие роли и создает для них Django группы
    """
    print("\n🎯 Проверка существующих ролей")
    print("=" * 60)
    
    roles = Role.objects.all()
    print(f"Найдено ролей: {roles.count()}")
    
    for role in roles:
        if not role.django_group:
            print(f"⚠️  Роль '{role.name}' не имеет Django группы, создаем...")
            role.save()  # Это вызовет сигнал и создаст группу
            print(f"✅ Создана группа для роли '{role.name}'")
        else:
            print(f"✅ Роль '{role.name}' уже имеет группу: {role.django_group.name}")

if __name__ == "__main__":
    print("🚀 Запуск тестирования синхронизации ролей")
    print("=" * 60)
    
    # Проверяем существующие роли
    test_existing_roles()
    
    # Тестируем синхронизацию
    success = test_role_group_sync()
    
    if success:
        print("\n✅ СИНХРОНИЗАЦИЯ РАБОТАЕТ КОРРЕКТНО!")
    else:
        print("\n❌ Есть проблемы с синхронизацией") 
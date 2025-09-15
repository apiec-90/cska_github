#!/usr/bin/env python
"""
Тесты для проверки подключения к Supabase и соответствия пользователей
"""
import os
import sys
import django
from django.conf import settings
from django.test import TestCase
from django.db import connection
from django.contrib.auth.models import User
from core.models import Staff, Athlete, Parent, TrainingGroup

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def test_database_connection():
    """Тест подключения к базе данных Supabase"""
    print("🔍 Тестирование подключения к Supabase...")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Подключение успешно! PostgreSQL версия: {version[0]}")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_tables_exist():
    """Тест существования всех необходимых таблиц"""
    print("\n🔍 Проверка существования таблиц...")
    
    required_tables = [
        'auth_user',
        'core_staff', 
        'core_athlete',
        'core_parent',
        'core_traininggroup',
        'core_paymentmethod',
        'core_athleteparent',
        'core_athletetraininggroup',
        'core_groupschedule',
        'core_trainingsession',
        'core_attendancerecord',
        'core_documenttype',
        'core_document',
        'core_payment',
        'core_auditrecord'
    ]
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
    
    missing_tables = []
    for table in required_tables:
        if table in existing_tables:
            print(f"✅ Таблица {table} существует")
        else:
            print(f"❌ Таблица {table} отсутствует")
            missing_tables.append(table)
    
    return len(missing_tables) == 0, missing_tables

def test_user_creation():
    """Тест создания пользователей в Supabase"""
    print("\n🔍 Тестирование создания пользователей...")
    
    try:
        # Создаем тестового пользователя
        test_user = User.objects.create_user(
            username='test_supabase_user',
            email='test@supabase.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"✅ Пользователь создан: {test_user.username}")
        
        # Проверяем, что пользователь сохранился в базе
        saved_user = User.objects.get(username='test_supabase_user')
        print(f"✅ Пользователь найден в базе: {saved_user.get_full_name()}")
        
        # Удаляем тестового пользователя
        test_user.delete()
        print("✅ Тестовый пользователь удален")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка создания пользователя: {e}")
        return False

def test_staff_creation():
    """Тест создания сотрудника"""
    print("\n🔍 Тестирование создания сотрудника...")
    
    try:
        # Создаем пользователя для сотрудника
        user = User.objects.create_user(
            username='test_staff',
            email='staff@supabase.com',
            password='testpass123',
            first_name='Staff',
            last_name='Test'
        )
        
        # Создаем сотрудника
        staff = Staff.objects.create(
            user=user,
            phone='+7-999-123-45-67',
            birth_date='1990-01-01',
            subrole='trainer'
        )
        print(f"✅ Сотрудник создан: {staff}")
        
        # Проверяем связь
        staff_from_db = Staff.objects.get(user=user)
        print(f"✅ Сотрудник найден в базе: {staff_from_db}")
        
        # Удаляем
        staff.delete()
        user.delete()
        print("✅ Тестовый сотрудник удален")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка создания сотрудника: {e}")
        return False

def test_athlete_creation():
    """Тест создания спортсмена"""
    print("\n🔍 Тестирование создания спортсмена...")
    
    try:
        # Создаем пользователя для спортсмена
        user = User.objects.create_user(
            username='test_athlete',
            email='athlete@supabase.com',
            password='testpass123',
            first_name='Athlete',
            last_name='Test'
        )
        
        # Создаем спортсмена
        athlete = Athlete.objects.create(
            user=user,
            phone='+7-999-123-45-68',
            birth_date='2010-01-01',
            gender='male'
        )
        print(f"✅ Спортсмен создан: {athlete}")
        
        # Проверяем связь
        athlete_from_db = Athlete.objects.get(user=user)
        print(f"✅ Спортсмен найден в базе: {athlete_from_db}")
        
        # Удаляем
        athlete.delete()
        user.delete()
        print("✅ Тестовый спортсмен удален")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка создания спортсмена: {e}")
        return False

def test_database_performance():
    """Тест производительности базы данных"""
    print("\n🔍 Тестирование производительности...")
    
    import time
    
    try:
        start_time = time.time()
        
        # Создаем 10 пользователей
        users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'perf_test_{i}',
                email=f'perf{i}@test.com',
                password='testpass123'
            )
            users.append(user)
        
        creation_time = time.time() - start_time
        print(f"✅ Создание 10 пользователей: {creation_time:.3f} сек")
        
        # Тест чтения
        start_time = time.time()
        User.objects.all().count()
        read_time = time.time() - start_time
        print(f"✅ Подсчет пользователей: {read_time:.3f} сек")
        
        # Удаляем тестовых пользователей
        for user in users:
            user.delete()
        
        print("✅ Тестовые пользователи удалены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования производительности: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов Supabase подключения\n")
    
    tests = [
        ("Подключение к базе данных", test_database_connection),
        ("Существование таблиц", test_tables_exist),
        ("Создание пользователей", test_user_creation),
        ("Создание сотрудников", test_staff_creation),
        ("Создание спортсменов", test_athlete_creation),
        ("Производительность", test_database_performance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"ТЕСТ: {test_name}")
        print('='*50)
        
        try:
            if test_name == "Существование таблиц":
                success, missing = test_func()
                if not success:
                    print(f"❌ Отсутствующие таблицы: {missing}")
            else:
                success = test_func()
            
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print(f"\n{'='*50}")
    print("ИТОГОВЫЙ ОТЧЕТ")
    print('='*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты успешно пройдены! Supabase подключение работает корректно.")
    else:
        print("⚠️  Некоторые тесты провалены. Проверьте настройки подключения.")

if __name__ == "__main__":
    main()

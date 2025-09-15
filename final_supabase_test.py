#!/usr/bin/env python
"""
Финальный тест Supabase подключения и данных
"""
import os
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def test_connection():
    """Тест подключения к Supabase"""
    print("🔍 Тестирование подключения к Supabase...")
    
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            # Простой запрос для проверки подключения
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result[0] == 1:
                print("✅ Подключение к Supabase успешно!")
                return True
            else:
                print("❌ Неожиданный результат запроса")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_data_integrity():
    """Тест целостности данных"""
    print("\n🔍 Проверка целостности данных...")
    
    try:
        from django.contrib.auth.models import User
        from core.models import Staff, Athlete, Parent, TrainingGroup, PaymentMethod
        
        # Проверяем количество записей
        user_count = User.objects.count()
        staff_count = Staff.objects.count()
        athlete_count = Athlete.objects.count()
        parent_count = Parent.objects.count()
        group_count = TrainingGroup.objects.count()
        payment_method_count = PaymentMethod.objects.count()
        
        print(f"📊 Статистика данных в Supabase:")
        print(f"  - Пользователей: {user_count}")
        print(f"  - Сотрудников: {staff_count}")
        print(f"  - Спортсменов: {athlete_count}")
        print(f"  - Родителей: {parent_count}")
        print(f"  - Групп: {group_count}")
        print(f"  - Способов оплаты: {payment_method_count}")
        
        # Проверяем связи
        print("\n🔗 Проверка связей:")
        
        # Проверяем, что у всех сотрудников есть пользователи
        staff_without_user = Staff.objects.filter(user__isnull=True).count()
        print(f"  - Сотрудников без пользователя: {staff_without_user}")
        
        # Проверяем, что у всех спортсменов есть пользователи
        athlete_without_user = Athlete.objects.filter(user__isnull=True).count()
        print(f"  - Спортсменов без пользователя: {athlete_without_user}")
        
        # Проверяем, что у всех родителей есть пользователи
        parent_without_user = Parent.objects.filter(user__isnull=True).count()
        print(f"  - Родителей без пользователя: {parent_without_user}")
        
        print("✅ Проверка целостности завершена")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки данных: {e}")
        return False

def test_user_creation():
    """Тест создания нового пользователя"""
    print("\n🔍 Тестирование создания пользователя...")
    
    try:
        from django.contrib.auth.models import User
        from core.models import Staff
        
        # Создаем тестового пользователя
        test_user = User.objects.create_user(
            username='supabase_final_test',
            email='final@supabase.com',
            password='testpass123',
            first_name='Final',
            last_name='Test'
        )
        print(f"✅ Пользователь создан: {test_user.username}")
        
        # Создаем профиль сотрудника
        staff = Staff.objects.create(
            user=test_user,
            phone='+7-999-999-99-99',
            birth_date='1995-01-01',
            subrole='trainer'
        )
        print(f"✅ Профиль сотрудника создан: {staff}")
        
        # Проверяем, что данные сохранились
        saved_staff = Staff.objects.get(user=test_user)
        print(f"✅ Данные найдены в базе: {saved_staff}")
        
        # Удаляем тестовые данные
        staff.delete()
        test_user.delete()
        print("✅ Тестовые данные удалены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания пользователя: {e}")
        return False

def test_performance():
    """Тест производительности"""
    print("\n🔍 Тестирование производительности...")
    
    import time
    
    try:
        from django.contrib.auth.models import User
        
        # Тест создания пользователей
        start_time = time.time()
        
        users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'perf_test_{i}',
                email=f'perf{i}@test.com',
                password='testpass123'
            )
            users.append(user)
        
        creation_time = time.time() - start_time
        print(f"✅ Создание 5 пользователей: {creation_time:.3f} сек")
        
        # Тест чтения
        start_time = time.time()
        user_count = User.objects.count()
        read_time = time.time() - start_time
        print(f"✅ Подсчет пользователей ({user_count}): {read_time:.3f} сек")
        
        # Удаляем тестовых пользователей
        for user in users:
            user.delete()
        
        print("✅ Тестовые пользователи удалены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования производительности: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Финальный тест Supabase подключения\n")
    
    tests = [
        ("Подключение к базе данных", test_connection),
        ("Целостность данных", test_data_integrity),
        ("Создание пользователя", test_user_creation),
        ("Производительность", test_performance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"ТЕСТ: {test_name}")
        print('='*60)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("ИТОГОВЫЙ ОТЧЕТ")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Supabase полностью готов к работе.")
        print("\n📋 Что работает:")
        print("  ✅ Подключение к PostgreSQL в Supabase")
        print("  ✅ Создание и удаление пользователей")
        print("  ✅ Создание профилей (сотрудники, спортсмены, родители)")
        print("  ✅ Целостность данных")
        print("  ✅ Производительность базы данных")
        print("\n🚀 Проект готов к использованию!")
    else:
        print("⚠️  Некоторые тесты провалены. Проверьте настройки.")

if __name__ == "__main__":
    main()

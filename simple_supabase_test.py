#!/usr/bin/env python
"""
Простой тест подключения к Supabase
"""
import os
import django
 

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def test_connection():
    """Тест подключения к Supabase"""
    print("🔍 Тестирование подключения к Supabase...")
    
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            # Проверяем версию PostgreSQL
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print("✅ Подключение успешно!")
            print(f"📊 PostgreSQL версия: {version[0][:50]}...")
            
            # Проверяем количество таблиц
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            print(f"📊 Количество таблиц: {table_count}")
            
            # Показываем основные таблицы
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name LIKE 'core_%'
                ORDER BY table_name
            """)
            core_tables = cursor.fetchall()
            print(f"📊 Таблицы приложения: {len(core_tables)}")
            for table in core_tables:
                print(f"  - {table[0]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_user_creation():
    """Тест создания пользователя"""
    print("\n🔍 Тестирование создания пользователя...")
    
    from django.contrib.auth.models import User
    
    try:
        # Создаем тестового пользователя
        test_user = User.objects.create_user(
            username='supabase_test_user',
            email='test@supabase.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"✅ Пользователь создан: {test_user.username}")
        
        # Проверяем, что пользователь сохранился
        saved_user = User.objects.get(username='supabase_test_user')
        print(f"✅ Пользователь найден в базе: {saved_user.get_full_name()}")
        
        # Удаляем тестового пользователя
        test_user.delete()
        print("✅ Тестовый пользователь удален")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания пользователя: {e}")
        return False

def test_models():
    """Тест моделей приложения"""
    print("\n🔍 Тестирование моделей приложения...")
    
    try:
        from core.models import Staff, Athlete, TrainingGroup, PaymentMethod
        from django.contrib.auth.models import User
        
        # Создаем пользователя для тестов
        user = User.objects.create_user(
            username='model_test_user',
            email='model@test.com',
            password='testpass123'
        )
        
        # Тест создания сотрудника
        staff = Staff.objects.create(
            user=user,
            phone='+7-999-123-45-67',
            birth_date='1990-01-01',
            subrole='trainer'
        )
        print(f"✅ Сотрудник создан: {staff}")
        
        # Тест создания спортсмена
        athlete_user = User.objects.create_user(
            username='athlete_test_user',
            email='athlete@test.com',
            password='testpass123'
        )
        
        athlete = Athlete.objects.create(
            user=athlete_user,
            phone='+7-999-123-45-68',
            birth_date='2010-01-01',
            gender='male'
        )
        print(f"✅ Спортсмен создан: {athlete}")
        
        # Тест создания группы
        group = TrainingGroup.objects.create(
            name='Тестовая группа',
            description='Группа для тестирования',
            max_participants=15
        )
        print(f"✅ Группа создана: {group}")
        
        # Тест создания способа оплаты
        payment_method = PaymentMethod.objects.create(
            name='Тестовый способ оплаты'
        )
        print(f"✅ Способ оплаты создан: {payment_method}")
        
        # Удаляем тестовые данные
        staff.delete()
        athlete.delete()
        athlete_user.delete()
        group.delete()
        payment_method.delete()
        user.delete()
        print("✅ Тестовые данные удалены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования моделей: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Запуск простых тестов Supabase\n")
    
    tests = [
        ("Подключение к базе данных", test_connection),
        ("Создание пользователя", test_user_creation),
        ("Тестирование моделей", test_models),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"ТЕСТ: {test_name}")
        print('='*50)
        
        try:
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
        print("🎉 Все тесты успешно пройдены! Supabase работает корректно.")
    else:
        print("⚠️  Некоторые тесты провалены. Проверьте настройки.")

if __name__ == "__main__":
    main()

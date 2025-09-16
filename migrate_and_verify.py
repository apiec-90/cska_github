#!/usr/bin/env python
"""
Скрипт для выполнения миграций и проверки данных в Supabase
"""
import os
import django
from django.core.management import call_command
from django.db import connection, transaction

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def run_migrations():
    """Выполнение миграций"""
    print("🔄 Выполнение миграций...")
    
    try:
        # Показываем текущие миграции
        print("\n📋 Текущие миграции:")
        call_command('showmigrations')
        
        # Применяем миграции
        print("\n🔄 Применение миграций...")
        call_command('migrate', verbosity=2)
        
        print("✅ Миграции успешно применены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграций: {e}")
        return False

def verify_database_structure():
    """Проверка структуры базы данных"""
    print("\n🔍 Проверка структуры базы данных...")
    
    with connection.cursor() as cursor:
        # Получаем все таблицы
        cursor.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"📊 Найдено таблиц: {len(tables)}")
        for table_name, table_type in tables:
            print(f"  - {table_name}")
        
        # Проверяем основные таблицы Django
        django_tables = [
            'django_migrations',
            'django_content_type',
            'django_session',
            'auth_user',
            'auth_group',
            'auth_permission',
            'django_admin_log'
        ]
        
        print("\n🔍 Проверка Django таблиц:")
        for table in django_tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                )
            """)
            exists = cursor.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"  {status} {table}")
        
        # Проверяем таблицы приложения
        app_tables = [
            'core_staff',
            'core_athlete', 
            'core_parent',
            'core_traininggroup',
            'core_paymentmethod'
        ]
        
        print("\n🔍 Проверка таблиц приложения:")
        for table in app_tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                )
            """)
            exists = cursor.fetchone()[0]
            status = "✅" if exists else "❌"
            print(f"  {status} {table}")

def create_test_data():
    """Создание тестовых данных"""
    print("\n📝 Создание тестовых данных...")
    
    from django.contrib.auth.models import User
    from core.models import Staff, Athlete, Parent, TrainingGroup, PaymentMethod
    
    try:
        with transaction.atomic():
            # Создаем способы оплаты
            payment_methods = [
                'Наличные',
                'Банковская карта',
                'Перевод на карту',
                'СБП'
            ]
            
            for method_name in payment_methods:
                method, created = PaymentMethod.objects.get_or_create(
                    name=method_name,
                    defaults={'is_active': True}
                )
                if created:
                    print(f"✅ Создан способ оплаты: {method_name}")
            
            # Создаем тестового тренера
            trainer_user, created = User.objects.get_or_create(
                username='trainer_test',
                defaults={
                    'email': 'trainer@test.com',
                    'first_name': 'Иван',
                    'last_name': 'Тренеров',
                    'is_active': True
                }
            )
            
            if created:
                trainer_user.set_password('trainer123')
                trainer_user.save()
                print("✅ Создан тестовый тренер")
            
            trainer, created = Staff.objects.get_or_create(
                user=trainer_user,
                defaults={
                    'phone': '+7-999-111-22-33',
                    'birth_date': '1985-05-15',
                    'subrole': 'trainer'
                }
            )
            
            if created:
                print("✅ Создан профиль тренера")
            
            # Создаем тестовую группу
            group, created = TrainingGroup.objects.get_or_create(
                name='Тестовая группа',
                defaults={
                    'description': 'Группа для тестирования',
                    'max_participants': 15,
                    'is_active': True
                }
            )
            
            if created:
                print("✅ Создана тестовая группа")
            
            # Создаем тестового спортсмена
            athlete_user, created = User.objects.get_or_create(
                username='athlete_test',
                defaults={
                    'email': 'athlete@test.com',
                    'first_name': 'Петр',
                    'last_name': 'Спортсменов',
                    'is_active': True
                }
            )
            
            if created:
                athlete_user.set_password('athlete123')
                athlete_user.save()
                print("✅ Создан тестовый спортсмен")
            
            athlete, created = Athlete.objects.get_or_create(
                user=athlete_user,
                defaults={
                    'phone': '+7-999-222-33-44',
                    'birth_date': '2010-03-20',
                    'gender': 'male'
                }
            )
            
            if created:
                print("✅ Создан профиль спортсмена")
            
            # Создаем тестового родителя
            parent_user, created = User.objects.get_or_create(
                username='parent_test',
                defaults={
                    'email': 'parent@test.com',
                    'first_name': 'Мария',
                    'last_name': 'Родителева',
                    'is_active': True
                }
            )
            
            if created:
                parent_user.set_password('parent123')
                parent_user.save()
                print("✅ Создан тестовый родитель")
            
            parent, created = Parent.objects.get_or_create(
                user=parent_user,
                defaults={
                    'phone': '+7-999-333-44-55',
                    'birth_date': '1980-07-10'
                }
            )
            
            if created:
                print("✅ Создан профиль родителя")
            
            print("✅ Тестовые данные успешно созданы")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка создания тестовых данных: {e}")
        return False

def verify_data_integrity():
    """Проверка целостности данных"""
    print("\n🔍 Проверка целостности данных...")
    
    from django.contrib.auth.models import User
    from core.models import Staff, Athlete, Parent, TrainingGroup, PaymentMethod
    
    try:
        # Проверяем количество записей
        user_count = User.objects.count()
        staff_count = Staff.objects.count()
        athlete_count = Athlete.objects.count()
        parent_count = Parent.objects.count()
        group_count = TrainingGroup.objects.count()
        payment_method_count = PaymentMethod.objects.count()
        
        print("📊 Статистика данных:")
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
        print(f"❌ Ошибка проверки целостности: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Запуск миграций и проверки Supabase\n")
    
    steps = [
        ("Выполнение миграций", run_migrations),
        ("Проверка структуры БД", verify_database_structure),
        ("Создание тестовых данных", create_test_data),
        ("Проверка целостности", verify_data_integrity),
    ]
    
    results = []
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"ШАГ: {step_name}")
        print('='*60)
        
        try:
            success = step_func()
            results.append((step_name, success))
        except Exception as e:
            print(f"❌ Критическая ошибка в шаге {step_name}: {e}")
            results.append((step_name, False))
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("ИТОГОВЫЙ ОТЧЕТ")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for step_name, success in results:
        status = "✅ УСПЕШНО" if success else "❌ ОШИБКА"
        print(f"{step_name}: {status}")
    
    print(f"\nРезультат: {passed}/{total} шагов выполнено успешно")
    
    if passed == total:
        print("🎉 Все шаги выполнены успешно! Supabase готов к работе.")
    else:
        print("⚠️  Некоторые шаги завершились с ошибками.")

if __name__ == "__main__":
    main()

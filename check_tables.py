#!/usr/bin/env python
"""
Проверка таблиц в Supabase
"""
import os
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def check_tables():
    """Проверка существующих таблиц"""
    from django.db import connection
    
    print("🔍 Проверка таблиц в Supabase...")
    
    try:
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
            print("\n📋 Список таблиц:")
            for table_name, table_type in tables:
                print(f"  - {table_name}")
            
            # Проверяем основные Django таблицы
            django_tables = [
                'django_migrations',
                'django_content_type', 
                'django_session',
                'auth_user',
                'auth_group',
                'auth_permission',
                'django_admin_log'
            ]
            
            print("\n🔍 Django таблицы:")
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
            
            print("\n🔍 Таблицы приложения:")
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
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка проверки таблиц: {e}")
        return False

def check_data():
    """Проверка данных в таблицах"""
    print("\n🔍 Проверка данных...")
    
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
        
        print(f"📊 Статистика данных:")
        print(f"  - Пользователей: {user_count}")
        print(f"  - Сотрудников: {staff_count}")
        print(f"  - Спортсменов: {athlete_count}")
        print(f"  - Родителей: {parent_count}")
        print(f"  - Групп: {group_count}")
        print(f"  - Способов оплаты: {payment_method_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки данных: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Проверка таблиц Supabase\n")
    
    check_tables()
    check_data()
    
    print("\n✅ Проверка завершена")

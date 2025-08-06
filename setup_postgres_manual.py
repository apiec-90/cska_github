#!/usr/bin/env python
"""
Скрипт для ручной настройки PostgreSQL
Выполните эти команды в psql или pgAdmin
"""

def print_setup_instructions():
    """Выводит инструкции по настройке PostgreSQL"""
    
    print("=" * 60)
    print("НАСТРОЙКА POSTGRESQL")
    print("=" * 60)
    
    print("\n1. Откройте psql или pgAdmin")
    print("2. Выполните следующие команды:")
    print()
    
    print("-- Создание базы данных")
    print("CREATE DATABASE cska_sports_db ENCODING 'UTF8';")
    print()
    
    print("-- Подключение к созданной БД")
    print("\\c cska_sports_db")
    print()
    
    print("-- Импорт схемы из import.sql")
    print("\\i import.sql")
    print()
    
    print("3. После создания БД обновите настройки Django:")
    print("   - Откройте cska_django_supabase/settings.py")
    print("   - Измените DATABASES на PostgreSQL")
    print()
    
    print("4. Примените миграции Django:")
    print("   python manage.py migrate")
    print()
    
    print("5. Создайте суперпользователя:")
    print("   python manage.py createsuperuser")
    print()
    
    print("=" * 60)

def create_django_settings_update():
    """Создает обновленные настройки Django для PostgreSQL"""
    
    settings_content = '''
# Обновите эти настройки в cska_django_supabase/settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cska_sports_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
'''
    
    print("\n" + "=" * 60)
    print("ОБНОВЛЕННЫЕ НАСТРОЙКИ DJANGO")
    print("=" * 60)
    print(settings_content)

if __name__ == "__main__":
    print_setup_instructions()
    create_django_settings_update() 
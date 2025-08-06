#!/usr/bin/env python
import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def check_postgresql():
    """Проверяет доступность PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="postgres"
        )
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False

def create_database():
    """Создает базу данных"""
    try:
        # Подключаемся к postgres для создания БД
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="postgres",
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Проверяем существует ли БД
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='cska_sports_school'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE cska_sports_school")
            print("✅ База данных cska_sports_school создана")
        else:
            print("✅ База данных cska_sports_school уже существует")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания базы данных: {e}")
        return False

def execute_sql_file():
    """Выполняет SQL файл для создания схемы"""
    try:
        # Подключаемся к созданной БД
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="postgres",
            database="cska_sports_school"
        )
        cursor = conn.cursor()
        
        # Читаем SQL файл
        with open('create_local_db.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Разбиваем на отдельные команды
        commands = sql_content.split(';')
        
        for command in commands:
            command = command.strip()
            if command and not command.startswith('--') and not command.startswith('\c'):
                try:
                    cursor.execute(command)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"⚠️  Предупреждение при выполнении команды: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Схема базы данных создана")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка выполнения SQL файла: {e}")
        return False

def main():
    print("🚀 Настройка локальной PostgreSQL базы данных")
    print("=" * 50)
    
    # Проверяем PostgreSQL
    if not check_postgresql():
        print("❌ PostgreSQL недоступен. Убедитесь что:")
        print("   1. PostgreSQL установлен")
        print("   2. Сервис запущен")
        print("   3. Пользователь postgres с паролем postgres существует")
        return False
    
    # Создаем БД
    if not create_database():
        return False
    
    # Выполняем SQL файл
    if not execute_sql_file():
        return False
    
    print("\n✅ Локальная база данных настроена успешно!")
    print("📋 Следующие шаги:")
    print("   1. python manage.py makemigrations")
    print("   2. python manage.py migrate")
    print("   3. python create_superuser.py")
    print("   4. python manage.py runserver")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 
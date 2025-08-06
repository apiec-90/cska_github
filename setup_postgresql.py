import psycopg2
import os
from pathlib import Path

def setup_database():
    """Настройка PostgreSQL базы данных"""
    
    # Параметры подключения
    DB_NAME = 'cska_sports_db'
    DB_USER = 'postgres'
    DB_PASSWORD = 'postgres'
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    
    try:
        # Подключаемся к PostgreSQL для создания БД
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database='postgres',  # Подключаемся к системной БД
            client_encoding='utf8'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Проверяем существование БД
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Создаем базу данных {DB_NAME}...")
            cursor.execute(f"CREATE DATABASE {DB_NAME} ENCODING 'UTF8'")
            print(f"База данных {DB_NAME} создана успешно")
        else:
            print(f"База данных {DB_NAME} уже существует")
        
        cursor.close()
        conn.close()
        
        # Теперь подключаемся к созданной БД и импортируем схему
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            client_encoding='utf8'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Читаем и выполняем SQL из import.sql
        sql_file = Path(__file__).parent / 'import.sql'
        if sql_file.exists():
            print("Импортируем схему из import.sql...")
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Разбиваем на отдельные команды
            commands = sql_content.split(';')
            for command in commands:
                command = command.strip()
                if command:
                    try:
                        cursor.execute(command)
                        print(f"Выполнена команда: {command[:50]}...")
                    except Exception as e:
                        print(f"Ошибка при выполнении команды: {e}")
                        print(f"Команда: {command}")
            
            print("Схема импортирована успешно")
        else:
            print("Файл import.sql не найден")
        
        cursor.close()
        conn.close()
        
        print("Настройка базы данных завершена успешно!")
        
    except Exception as e:
        print(f"Ошибка при настройке базы данных: {e}")
        print("Убедитесь, что PostgreSQL запущен и доступен")

if __name__ == "__main__":
    setup_database() 
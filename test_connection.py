import psycopg2
import sys

def test_connection():
    """Тестирование подключения к PostgreSQL"""
    
    # Параметры подключения
    DB_NAME = 'cska_sports_db'
    DB_USER = 'postgres'
    DB_PASSWORD = 'postgres'
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    
    try:
        # Пробуем подключиться к системной БД
        print("Тестируем подключение к PostgreSQL...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database='postgres'
        )
        print("✓ Подключение к PostgreSQL успешно!")
        
        cursor = conn.cursor()
        
        # Проверяем существование нашей БД
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"✓ База данных {DB_NAME} существует")
        else:
            print(f"✗ База данных {DB_NAME} не существует")
            print("Создайте БД вручную командой:")
            print(f"CREATE DATABASE {DB_NAME} ENCODING 'UTF8';")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
        print("\nУбедитесь, что:")
        print("1. PostgreSQL установлен и запущен")
        print("2. Пользователь 'postgres' существует")
        print("3. Пароль 'postgres' правильный")
        print("4. PostgreSQL слушает на localhost:5432")

if __name__ == "__main__":
    test_connection() 
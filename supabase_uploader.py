import os
from supabase import create_client
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки по умолчанию
SUPABASE_STORAGE_BUCKET = "media"  # Имя bucket в Supabase
UPLOAD_FOLDER = "media"  # Локальная папка с файлами для загрузки

def upload_to_supabase():
    """Загрузка файлов в Supabase Storage"""
    # Получаем настройки Supabase из переменных окружения или используем значения по умолчанию
    supabase_url = os.getenv("SUPABASE_URL", "https://gzrefdsqgynnvdodubiu.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cmVmZHNxZ3lubnZkb2R1Yml1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NjA3NzUsImV4cCI6MjA2OTQzNjc3NX0.cSowcQkvY5uEb20pkNWuA0LxYfX0VJfd6maCxjCKcg0")
    
    try:
        # Создаем клиент Supabase
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Подключение к Supabase установлено")
        
        # Проверяем доступность bucket и получаем список всех buckets
        try:
            buckets = supabase.storage.list_buckets()
            print(f"📦 Доступные buckets: {[b.name for b in buckets]}")
        except Exception as e:
            print(f"⚠️ Не удалось получить список buckets: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Supabase: {e}")
        return
    
    # Настройки для загрузки файлов - получаем из переменных окружения
    bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", SUPABASE_STORAGE_BUCKET)  # Имя bucket в Supabase
    upload_folder = os.getenv("UPLOAD_FOLDER", UPLOAD_FOLDER)  # Локальная папка с файлами для загрузки
    
    print("🔧 Настройки:")
    print(f"   Bucket: '{bucket_name}'")
    print(f"   Папка: '{upload_folder}'")
    
    # Проверяем существование локальной папки
    if not os.path.exists(upload_folder):
        print(f"❌ Папка {upload_folder} не существует")
        print(f"💡 Создайте папку '{upload_folder}' или измените UPLOAD_FOLDER в .env")
        return
    
    # Проверяем существование bucket в Supabase
    try:
        supabase.storage.get_bucket(bucket_name)
        print(f"✅ Bucket '{bucket_name}' найден")
    except Exception as e:
        print(f"❌ Bucket '{bucket_name}' не найден: {e}")
        print(f"💡 Создайте bucket '{bucket_name}' в Supabase Dashboard")
        print("💡 Или измените SUPABASE_STORAGE_BUCKET в .env")
        return
    
    print(f"📁 Начинаем загрузку файлов из папки: {upload_folder}")
    
    # Обходим все файлы в папке и подпапках
    uploaded_count = 0
    error_count = 0
    
    for root, _, files in os.walk(upload_folder):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, upload_folder)
            
            try:
                # Читаем файл и загружаем в Supabase
                with open(file_path, "rb") as f:
                    # Заменяем обратные слеши на прямые для Supabase (проблема Windows)
                    supabase_path = relative_path.replace("\\", "/")
                    # Используем правильный синтаксис для загрузки
                    supabase.storage.from_(bucket_name).upload(supabase_path, f.read())
                    print(f"✅ Успешно: {supabase_path}")
                    uploaded_count += 1
            except Exception as e:
                print(f"❌ Ошибка в {relative_path}: {e}")
                error_count += 1
    
    print("\n📊 Результат загрузки:")
    print(f"✅ Загружено: {uploaded_count} файлов")
    print(f"❌ Ошибок: {error_count} файлов")

def create_bucket_if_not_exists():
    """Создание bucket если он не существует"""
    supabase_url = os.getenv("SUPABASE_URL", "https://gzrefdsqgynnvdodubiu.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cmVmZHNxZ3lubnZkb2R1Yml1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NjA3NzUsImV4cCI6MjA2OTQzNjc3NX0.cSowcQkvY5uEb20pkNWuA0LxYfX0VJfd6maCxjCKcg0")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", SUPABASE_STORAGE_BUCKET)
        
        # Проверяем существование bucket
        try:
            supabase.storage.get_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' уже существует")
            return True
        except Exception:
            print(f"🔄 Создаем bucket '{bucket_name}'...")
            
            # Создаем bucket без параметра public (исправлено)
            try:
                supabase.storage.create_bucket(bucket_name)
                print(f"✅ Bucket '{bucket_name}' создан успешно")
                return True
            except Exception as e:
                print(f"❌ Не удалось создать bucket: {e}")
                print("💡 Создайте bucket вручную в Supabase Dashboard")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def check_bucket_status():
    """Проверка статуса bucket"""
    supabase_url = os.getenv("SUPABASE_URL", "https://gzrefdsqgynnvdodubiu.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cmVmZHNxZ3lubnZkb2R1Yml1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NjA3NzUsImV4cCI6MjA2OTQzNjc3NX0.cSowcQkvY5uEb20pkNWuA0LxYfX0VJfd6maCxjCKcg0")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Получаем список всех buckets
        buckets = supabase.storage.list_buckets()
        print(f"📦 Все доступные buckets: {[b.name for b in buckets]}")
        
        # Проверяем целевой bucket
        bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", SUPABASE_STORAGE_BUCKET)
        try:
            supabase.storage.get_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' найден и доступен")
            return True
        except Exception as e:
            print(f"❌ Bucket '{bucket_name}' не найден: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск Supabase Uploader...")
    
    # Проверяем статус bucket
    if check_bucket_status():
        # Затем загружаем файлы
        upload_to_supabase()
    else:
        print("❌ Bucket недоступен. Проверьте настройки Supabase.")
        print("💡 Создайте bucket в Supabase Dashboard или измените SUPABASE_STORAGE_BUCKET")
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def upload_to_supabase():
    supabase = create_client(
        os.getenv("https://gzrefdsqgynnvdodubiu.supabase.co"),
        os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cmVmZHNxZ3lubnZkb2R1Yml1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NjA3NzUsImV4cCI6MjA2OTQzNjc3NX0.cSowcQkvY5uEb20pkNWuA0LxYfX0VJfd6maCxjCKcg0")
    )
    
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "media")
    upload_folder = "media"  # Укажите свою папку
    
    for root, _, files in os.walk(upload_folder):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                try:
                    supabase.storage.from_(bucket).upload(file_path, f)
                    print(f"✅ Успешно: {file_path}")
                except Exception as e:
                    print(f"❌ Ошибка в {file_path}: {e}")

if __name__ == "__main__":
    upload_to_supabase()
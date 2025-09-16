"""
Утилиты для работы с Supabase Storage
"""
import os
from typing import Optional, Tuple
from django.conf import settings


def upload_to_supabase_storage(file_data: bytes, file_path: str) -> Tuple[bool, str]:
    """
    Загрузка файла в Supabase Storage
    
    Args:
        file_data: Данные файла в байтах
        file_path: Путь к файлу в storage (например, 'avatars/athlete_1_abc123.jpg')
    
    Returns:
        Tuple[bool, str]: (успех, сообщение об ошибке или URL файла)
    """
    try:
        from supabase import create_client
        
        # Получаем настройки Supabase
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        bucket_name = os.environ.get('SUPABASE_STORAGE_BUCKET', 'media')
        
        if not supabase_url or not supabase_key:
            return False, "Supabase credentials not configured"
        
        # Создаем клиент Supabase
        supabase = create_client(supabase_url, supabase_key)
        
        # Загружаем файл
        try:
            # Используем правильный синтаксис для загрузки
            result = supabase.storage.from_(bucket_name).upload(file_path, file_data)
            
            # Формируем публичный URL файла
            public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
            return True, public_url
            
        except Exception as upload_error:
            return False, f"Upload error: {str(upload_error)}"
            
    except ImportError:
        return False, "Supabase client not installed"
    except Exception as e:
        return False, f"Supabase upload error: {str(e)}"


def delete_from_supabase_storage(file_path: str) -> bool:
    """
    Удаление файла из Supabase Storage
    
    Args:
        file_path: Путь к файлу в storage
    
    Returns:
        bool: Успех операции
    """
    try:
        from supabase import create_client
        
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        bucket_name = os.environ.get('SUPABASE_STORAGE_BUCKET', 'media')
        
        if not supabase_url or not supabase_key:
            return False
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Удаляем файл
        result = supabase.storage.from_(bucket_name).remove([file_path])
        return bool(result)
        
    except Exception:
        return False


def get_supabase_file_url(file_path: str) -> Optional[str]:
    """
    Получение публичного URL файла в Supabase Storage
    
    Args:
        file_path: Путь к файлу в storage
    
    Returns:
        str или None: URL файла или None если не удалось получить
    """
    try:
        from supabase import create_client
        
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        bucket_name = os.environ.get('SUPABASE_STORAGE_BUCKET', 'media')
        
        if not supabase_url or not supabase_key:
            return None
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Получаем публичный URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        return public_url
        
    except Exception:
        return None

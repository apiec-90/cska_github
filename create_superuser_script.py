#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    """Создание суперпользователя"""
    try:
        # Проверяем, существует ли уже суперпользователь
        if User.objects.filter(is_superuser=True).exists():
            print("Суперпользователь уже существует")
            return
        
        # Создаем суперпользователя
        username = 'admin'
        email = 'admin@example.com'
        password = 'admin123'
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True
        )
        
        print(f"Суперпользователь создан успешно!")
        print(f"Логин: {username}")
        print(f"Пароль: {password}")
        print(f"Email: {email}")
        
    except Exception as e:
        print(f"Ошибка при создании суперпользователя: {e}")

if __name__ == "__main__":
    create_superuser() 
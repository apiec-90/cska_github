#!/usr/bin/env python
"""
Скрипт для создания тестовых данных
Запуск: python create_test_data.py
"""

import os
import sys
import django
from datetime import date, time

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sportcrm.settings')
django.setup()

from groups.models import Group
from athletes.models import Athlete
from attendance.models import Attendance
from payments.models import Payment

def create_test_data():
    """Создание тестовых данных"""
    print("Создание тестовых данных...")
    
    # Создаем группы
    group1, created = Group.objects.get_or_create(
        number=1,
        defaults={
            'age_min': 8,
            'age_max': 10,
            'trainer': 'Иванов И.И.',
            'days': ['mon', 'wed', 'fri'],
            'time': time(16, 0),
            'is_active': True
        }
    )
    
    group2, created = Group.objects.get_or_create(
        number=2,
        defaults={
            'age_min': 12,
            'age_max': 14,
            'trainer': 'Петров П.П.',
            'days': ['tue', 'thu', 'sat'],
            'time': time(17, 30),
            'is_active': True
        }
    )
    
    print(f"Группы созданы: {Group.objects.count()}")
    
    # Создаем спортсменов
    athletes_data = [
        {'first_name': 'Алексей', 'last_name': 'Смирнов', 'group': group1, 'birth_date': date(2015, 3, 15), 'phone': '+7-999-123-45-67'},
        {'first_name': 'Мария', 'last_name': 'Козлова', 'group': group1, 'birth_date': date(2014, 7, 22), 'phone': '+7-999-234-56-78'},
        {'first_name': 'Дмитрий', 'last_name': 'Новиков', 'group': group2, 'birth_date': date(2012, 11, 8), 'phone': '+7-999-345-67-89'},
        {'first_name': 'Анна', 'last_name': 'Морозова', 'group': group2, 'birth_date': date(2013, 5, 12), 'phone': '+7-999-456-78-90'},
    ]
    
    for athlete_data in athletes_data:
        athlete, created = Athlete.objects.get_or_create(
            phone=athlete_data['phone'],
            defaults=athlete_data
        )
    
    print(f"Спортсмены созданы: {Athlete.objects.count()}")
    
    # Создаем записи посещаемости
    athletes = Athlete.objects.all()
    test_dates = [date(2024, 1, 15), date(2024, 1, 17), date(2024, 1, 19)]
    
    for athlete in athletes:
        for test_date in test_dates:
            attendance, created = Attendance.objects.get_or_create(
                athlete=athlete,
                date=test_date,
                defaults={'status': 'present'}
            )
    
    print(f"Записи посещаемости созданы: {Attendance.objects.count()}")
    
    # Создаем записи оплаты
    payment_month = date(2024, 1, 1)
    
    for athlete in athletes:
        payment, created = Payment.objects.get_or_create(
            athlete=athlete,
            month=payment_month,
            defaults={
                'amount': 5000.00,
                'paid_amount': 3000.00,
                'status': 'partial'
            }
        )
    
    print(f"Записи оплаты созданы: {Payment.objects.count()}")
    
    print("\n✅ Тестовые данные созданы успешно!")
    print("\nДоступные URL:")
    print("- Главная: http://127.0.0.1:8000/")
    print("- Журнал посещаемости: http://127.0.0.1:8000/attendance/")
    print("- Система оплаты: http://127.0.0.1:8000/payments/")
    print("- Админка: http://127.0.0.1:8000/admin/")

if __name__ == "__main__":
    create_test_data() 
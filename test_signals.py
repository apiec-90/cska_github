#!/usr/bin/env python
"""
Тестовый файл для проверки работы сигналов и утилит
Запуск: python test_signals.py
"""

import os
import sys
import django
from datetime import date, time

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from core.models import TrainingGroup, GroupSchedule, TrainingSession
from core.utils.sessions import resync_future_sessions_for_group, ensure_month_sessions_for_group

def test_weekday_conversion():
    """Тест преобразования weekday"""
    print("=== Тест преобразования weekday ===")
    
    # Создаем тестовую группу
    group, created = TrainingGroup.objects.get_or_create(
        name="Тестовая группа для сигналов",
        defaults={
            'age_min': 10,
            'age_max': 15,
            'is_active': True
        }
    )
    
    if created:
        print(f"Создана тестовая группа: {group}")
    
    # Создаем расписание (понедельник = 1, время 10:00-11:00)
    schedule, created = GroupSchedule.objects.get_or_create(
        training_group=group,
        weekday=1,  # Понедельник
        start_time=time(10, 0),
        end_time=time(11, 0)
    )
    
    if created:
        print(f"Создано расписание: {schedule}")
    
    # Проверяем преобразование weekday
    python_weekday = schedule.weekday - 1  # 1 -> 0 (понедельник в Python)
    print(f"weekday в модели: {schedule.weekday} (понедельник)")
    print(f"python_weekday: {python_weekday} (понедельник в Python)")
    
    # Тестируем создание сессий
    print("\n=== Тест создания сессий ===")
    created_count = ensure_month_sessions_for_group(group)
    print(f"Создано сессий: {created_count}")
    
    # Проверяем созданные сессии
    sessions = TrainingSession.objects.filter(training_group=group)
    print(f"Всего сессий в группе: {sessions.count()}")
    
    for session in sessions[:5]:  # Показываем первые 5
        print(f"  Сессия: {session.date} {session.start_time}-{session.end_time}")
    
    # Тестируем пересборку
    print("\n=== Тест пересборки сессий ===")
    resync_future_sessions_for_group(group)
    print("Пересборка завершена")
    
    # Очистка
    print("\n=== Очистка ===")
    TrainingSession.objects.filter(training_group=group).delete()
    GroupSchedule.objects.filter(training_group=group).delete()
    group.delete()
    print("Тестовые данные удалены")

if __name__ == "__main__":
    test_weekday_conversion()

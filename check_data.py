#!/usr/bin/env python
"""
Проверка данных в Supabase
"""
import os
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def check_data():
    """Проверка данных в базе"""
    from django.contrib.auth.models import User
    from core.models import Athlete, Parent, TrainingGroup, Staff, Trainer, PaymentMethod
    
    print("🔍 Проверка данных в Supabase...")
    
    try:
        # Проверяем количество записей
        user_count = User.objects.count()
        athlete_count = Athlete.objects.count()
        parent_count = Parent.objects.count()
        group_count = TrainingGroup.objects.count()
        staff_count = Staff.objects.count()
        trainer_count = Trainer.objects.count()
        payment_method_count = PaymentMethod.objects.count()
        
        print(f"📊 Статистика данных:")
        print(f"  - Пользователей: {user_count}")
        print(f"  - Спортсменов: {athlete_count}")
        print(f"  - Родителей: {parent_count}")
        print(f"  - Групп: {group_count}")
        print(f"  - Сотрудников: {staff_count}")
        print(f"  - Тренеров: {trainer_count}")
        print(f"  - Способов оплаты: {payment_method_count}")
        
        # Проверяем конкретные записи
        if user_count > 0:
            print(f"\n👥 Пользователи:")
            for user in User.objects.all()[:5]:  # Показываем первых 5
                print(f"  - {user.username} ({user.first_name} {user.last_name})")
        
        if athlete_count > 0:
            print(f"\n⚽ Спортсмены:")
            for athlete in Athlete.objects.all()[:5]:
                print(f"  - {athlete}")
        
        if parent_count > 0:
            print(f"\n👨‍👩‍👧‍👦 Родители:")
            for parent in Parent.objects.all()[:5]:
                print(f"  - {parent}")
        
        if group_count > 0:
            print(f"\n🏃 Группы:")
            for group in TrainingGroup.objects.all()[:5]:
                print(f"  - {group}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки данных: {e}")
        return False

if __name__ == "__main__":
    check_data()

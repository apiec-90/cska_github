#!/usr/bin/env python
"""
Создание исправленных тестовых данных для Supabase
"""
import os
import django
from datetime import date, timedelta, time, datetime

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def create_payment_methods():
    """Создание способов оплаты"""
    print("💰 Создание способов оплаты...")
    
    from core.models import PaymentMethod
    
    payment_methods = [
        {'name': 'Наличные', 'is_active': True},
        {'name': 'Банковская карта', 'is_active': True},
        {'name': 'Перевод на карту', 'is_active': True},
        {'name': 'СБП (Система быстрых платежей)', 'is_active': True},
        {'name': 'Безналичный расчет', 'is_active': True},
    ]
    
    created_count = 0
    for method_data in payment_methods:
        method, created = PaymentMethod.objects.get_or_create(
            name=method_data['name'],
            defaults={'is_active': method_data['is_active']}
        )
        if created:
            created_count += 1
            print(f"  ✅ Создан способ оплаты: {method.name}")
    
    print(f"📊 Создано способов оплаты: {created_count}")
    return created_count

def create_trainers():
    """Создание тренеров"""
    print("\n🏃 Создание тренеров...")
    
    from django.contrib.auth.models import User
    from core.models import Trainer
    
    trainers_data = [
        {
            'username': 'main_trainer',
            'email': 'main_trainer@cska.com',
            'first_name': 'Александр',
            'last_name': 'Петров',
            'phone': '+7-999-300-00-01',
            'birth_date': date(1980, 3, 15)
        },
        {
            'username': 'trainer2',
            'email': 'trainer2@cska.com',
            'first_name': 'Михаил',
            'last_name': 'Иванов',
            'phone': '+7-999-300-00-02',
            'birth_date': date(1985, 7, 22)
        },
        {
            'username': 'trainer3',
            'email': 'trainer3@cska.com',
            'first_name': 'Дмитрий',
            'last_name': 'Сидоров',
            'phone': '+7-999-300-00-03',
            'birth_date': date(1988, 11, 8)
        }
    ]
    
    created_count = 0
    for trainer_info in trainers_data:
        user, user_created = User.objects.get_or_create(
            username=trainer_info['username'],
            defaults={
                'email': trainer_info['email'],
                'first_name': trainer_info['first_name'],
                'last_name': trainer_info['last_name'],
                'is_active': True
            }
        )
        
        if user_created:
            user.set_password('trainer123')
            user.save()
        
        trainer, trainer_created = Trainer.objects.get_or_create(
            user=user,
            defaults={
                'phone': trainer_info['phone'],
                'birth_date': trainer_info['birth_date']
            }
        )
        
        if trainer_created:
            created_count += 1
            print(f"  ✅ Создан тренер: {trainer}")
    
    print(f"📊 Создано тренеров: {created_count}")
    return created_count

def create_staff_members():
    """Создание сотрудников"""
    print("\n👨‍💼 Создание сотрудников...")
    
    from django.contrib.auth.models import User
    from core.models import Staff
    
    staff_data = [
        {
            'username': 'director',
            'email': 'director@cska.com',
            'first_name': 'Елена',
            'last_name': 'Морозова',
            'phone': '+7-999-100-00-01',
            'birth_date': date(1975, 3, 15)
        },
        {
            'username': 'manager1',
            'email': 'manager1@cska.com',
            'first_name': 'Анна',
            'last_name': 'Козлова',
            'phone': '+7-999-100-00-02',
            'birth_date': date(1985, 7, 22)
        }
    ]
    
    created_count = 0
    for staff_info in staff_data:
        user, user_created = User.objects.get_or_create(
            username=staff_info['username'],
            defaults={
                'email': staff_info['email'],
                'first_name': staff_info['first_name'],
                'last_name': staff_info['last_name'],
                'is_active': True
            }
        )
        
        if user_created:
            user.set_password('staff123')
            user.save()
        
        staff, staff_created = Staff.objects.get_or_create(
            user=user,
            defaults={
                'phone': staff_info['phone'],
                'birth_date': staff_info['birth_date'],
                'role': 'manager'
            }
        )
        
        if staff_created:
            created_count += 1
            print(f"  ✅ Создан сотрудник: {staff}")
    
    print(f"📊 Создано сотрудников: {created_count}")
    return created_count

def create_parents():
    """Создание родителей"""
    print("\n👨‍👩‍👧‍👦 Создание родителей...")
    
    from django.contrib.auth.models import User
    from core.models import Parent
    
    parents_data = [
        {
            'username': 'parent1',
            'email': 'parent1@example.com',
            'first_name': 'Иван',
            'last_name': 'Смирнов',
            'phone': '+7-999-200-00-01',
            'birth_date': date(1985, 2, 14)
        },
        {
            'username': 'parent2',
            'email': 'parent2@example.com',
            'first_name': 'Мария',
            'last_name': 'Кузнецова',
            'phone': '+7-999-200-00-02',
            'birth_date': date(1987, 6, 8)
        },
        {
            'username': 'parent3',
            'email': 'parent3@example.com',
            'first_name': 'Алексей',
            'last_name': 'Попов',
            'phone': '+7-999-200-00-03',
            'birth_date': date(1983, 10, 30)
        },
        {
            'username': 'parent4',
            'email': 'parent4@example.com',
            'first_name': 'Екатерина',
            'last_name': 'Васильева',
            'phone': '+7-999-200-00-04',
            'birth_date': date(1989, 4, 17)
        },
        {
            'username': 'parent5',
            'email': 'parent5@example.com',
            'first_name': 'Сергей',
            'last_name': 'Новиков',
            'phone': '+7-999-200-00-05',
            'birth_date': date(1981, 12, 5)
        }
    ]
    
    created_count = 0
    for parent_info in parents_data:
        user, user_created = User.objects.get_or_create(
            username=parent_info['username'],
            defaults={
                'email': parent_info['email'],
                'first_name': parent_info['first_name'],
                'last_name': parent_info['last_name'],
                'is_active': True
            }
        )
        
        if user_created:
            user.set_password('parent123')
            user.save()
        
        parent, parent_created = Parent.objects.get_or_create(
            user=user,
            defaults={
                'phone': parent_info['phone'],
                'birth_date': parent_info['birth_date']
            }
        )
        
        if parent_created:
            created_count += 1
            print(f"  ✅ Создан родитель: {parent}")
    
    print(f"📊 Создано родителей: {created_count}")
    return created_count

def create_training_groups():
    """Создание тренировочных групп"""
    print("\n🏃 Создание тренировочных групп...")
    
    from core.models import TrainingGroup, Trainer
    
    # Получаем тренеров
    trainers = list(Trainer.objects.all())
    if not trainers:
        print("  ⚠️ Нет тренеров. Создаю тестового тренера...")
        from django.contrib.auth.models import User
        trainer_user = User.objects.create_user(
            username='test_trainer',
            email='test_trainer@cska.com',
            password='trainer123',
            first_name='Тестовый',
            last_name='Тренер'
        )
        trainer = Trainer.objects.create(
            user=trainer_user,
            phone='+7-999-999-99-99',
            birth_date=date(1980, 1, 1)
        )
        trainers = [trainer]
    
    groups_data = [
        {
            'name': 'Младшая группа (6-8 лет)',
            'age_min': 6,
            'age_max': 8,
            'max_athletes': 12,
            'trainer': trainers[0] if trainers else None,
            'is_active': True
        },
        {
            'name': 'Средняя группа (9-11 лет)',
            'age_min': 9,
            'age_max': 11,
            'max_athletes': 15,
            'trainer': trainers[1] if len(trainers) > 1 else trainers[0],
            'is_active': True
        },
        {
            'name': 'Старшая группа (12-14 лет)',
            'age_min': 12,
            'age_max': 14,
            'max_athletes': 18,
            'trainer': trainers[2] if len(trainers) > 2 else trainers[0],
            'is_active': True
        }
    ]
    
    created_count = 0
    for group_data in groups_data:
        group, created = TrainingGroup.objects.get_or_create(
            name=group_data['name'],
            defaults=group_data
        )
        if created:
            created_count += 1
            print(f"  ✅ Создана группа: {group.name}")
    
    print(f"📊 Создано групп: {created_count}")
    return created_count

def create_athletes():
    """Создание спортсменов"""
    print("\n⚽ Создание спортсменов...")
    
    from django.contrib.auth.models import User
    from core.models import Athlete, Parent, TrainingGroup
    
    # Получаем родителей и группы
    parents = list(Parent.objects.all())
    groups = list(TrainingGroup.objects.all())
    
    if not parents:
        print("  ⚠️ Нет родителей. Создаю тестового родителя...")
        parent_user = User.objects.create_user(
            username='test_parent',
            email='test_parent@example.com',
            password='parent123',
            first_name='Тестовый',
            last_name='Родитель'
        )
        parent = Parent.objects.create(
            user=parent_user,
            phone='+7-999-999-99-99',
            birth_date=date(1980, 1, 1)
        )
        parents = [parent]
    
    if not groups:
        print("  ⚠️ Нет групп. Создаю тестовую группу...")
        from core.models import Trainer
        trainer = Trainer.objects.first()
        group = TrainingGroup.objects.create(
            name='Тестовая группа',
            age_min=6,
            age_max=8,
            max_athletes=15,
            trainer=trainer
        )
        groups = [group]
    
    athletes_data = [
        {
            'username': 'athlete1',
            'email': 'athlete1@example.com',
            'first_name': 'Артем',
            'last_name': 'Смирнов',
            'phone': '+7-999-400-00-01',
            'birth_date': date(2015, 3, 10),
            'parent': parents[0] if parents else None,
            'group': groups[0] if groups else None
        },
        {
            'username': 'athlete2',
            'email': 'athlete2@example.com',
            'first_name': 'София',
            'last_name': 'Кузнецова',
            'phone': '+7-999-400-00-02',
            'birth_date': date(2014, 7, 22),
            'parent': parents[1] if len(parents) > 1 else parents[0],
            'group': groups[1] if len(groups) > 1 else groups[0]
        },
        {
            'username': 'athlete3',
            'email': 'athlete3@example.com',
            'first_name': 'Максим',
            'last_name': 'Попов',
            'phone': '+7-999-400-00-03',
            'birth_date': date(2013, 11, 5),
            'parent': parents[2] if len(parents) > 2 else parents[0],
            'group': groups[2] if len(groups) > 2 else groups[0]
        },
        {
            'username': 'athlete4',
            'email': 'athlete4@example.com',
            'first_name': 'Анастасия',
            'last_name': 'Васильева',
            'phone': '+7-999-400-00-04',
            'birth_date': date(2012, 4, 18),
            'parent': parents[3] if len(parents) > 3 else parents[0],
            'group': groups[0] if groups else None
        },
        {
            'username': 'athlete5',
            'email': 'athlete5@example.com',
            'first_name': 'Кирилл',
            'last_name': 'Новиков',
            'phone': '+7-999-400-00-05',
            'birth_date': date(2011, 9, 12),
            'parent': parents[4] if len(parents) > 4 else parents[0],
            'group': groups[1] if len(groups) > 1 else groups[0]
        }
    ]
    
    created_count = 0
    for athlete_info in athletes_data:
        user, user_created = User.objects.get_or_create(
            username=athlete_info['username'],
            defaults={
                'email': athlete_info['email'],
                'first_name': athlete_info['first_name'],
                'last_name': athlete_info['last_name'],
                'is_active': True
            }
        )
        
        if user_created:
            user.set_password('athlete123')
            user.save()
        
        athlete, athlete_created = Athlete.objects.get_or_create(
            user=user,
            defaults={
                'phone': athlete_info['phone'],
                'birth_date': athlete_info['birth_date']
            }
        )
        
        if athlete_created:
            created_count += 1
            print(f"  ✅ Создан спортсмен: {athlete}")
            
            # Связываем с родителем
            if athlete_info['parent']:
                from core.models import AthleteParent
                AthleteParent.objects.get_or_create(
                    athlete=athlete,
                    parent=athlete_info['parent']
                )
                print(f"    🔗 Связан с родителем: {athlete_info['parent']}")
            
            # Добавляем в группу
            if athlete_info['group']:
                from core.models import AthleteTrainingGroup
                AthleteTrainingGroup.objects.get_or_create(
                    athlete=athlete,
                    group=athlete_info['group']
                )
                print(f"    🏃 Добавлен в группу: {athlete_info['group']}")
    
    print(f"📊 Создано спортсменов: {created_count}")
    return created_count

def create_training_sessions():
    """Создание тренировочных сессий"""
    print("\n📅 Создание тренировочных сессий...")
    
    from core.models import TrainingSession, TrainingGroup
    from datetime import datetime, timedelta
    
    groups = TrainingGroup.objects.all()
    
    if not groups.exists():
        print("  ⚠️ Нет групп для создания сессий")
        return 0
    
    created_count = 0
    base_date = datetime.now().date()
    
    for group in groups:
        # Создаем сессии на следующие 2 недели
        for week in range(2):
            for day in range(2):  # 2 тренировки в неделю
                session_date = base_date + timedelta(weeks=week, days=day*3)
                
                session, created = TrainingSession.objects.get_or_create(
                    training_group=group,
                    date=session_date,
                    defaults={
                        'start_time': time(16, 0),  # 16:00
                        'end_time': time(17, 30),   # 17:30
                        'is_closed': False,
                        'is_canceled': False
                    }
                )
                
                if created:
                    created_count += 1
                    print(f"  ✅ Создана сессия: {group.name} - {session_date}")
    
    print(f"📊 Создано тренировочных сессий: {created_count}")
    return created_count

def create_payments():
    """Создание платежей"""
    print("\n💳 Создание платежей...")
    
    from core.models import Payment, Athlete, PaymentMethod
    from decimal import Decimal
    import random
    
    athletes = Athlete.objects.all()
    payment_methods = PaymentMethod.objects.all()
    
    if not athletes.exists():
        print("  ⚠️ Нет спортсменов для создания платежей")
        return 0
    
    if not payment_methods.exists():
        print("  ⚠️ Нет способов оплаты для создания платежей")
        return 0
    
    created_count = 0
    base_date = datetime.now().date()
    
    for athlete in athletes:
        # Создаем 1-2 платежа для каждого спортсмена
        num_payments = random.randint(1, 2)
        
        for i in range(num_payments):
            payment_date = base_date - timedelta(days=random.randint(1, 30))
            amount = Decimal(str(random.randint(2000, 5000)))
            payment_method = random.choice(payment_methods)
            
            payment, created = Payment.objects.get_or_create(
                athlete=athlete,
                amount=amount,
                payment_date=payment_date,
                defaults={
                    'payment_method': payment_method,
                    'status': 'completed',
                    'notes': f'Оплата за тренировки - {payment_date.strftime("%B %Y")}'
                }
            )
            
            if created:
                created_count += 1
                print(f"  ✅ Создан платеж: {athlete} - {amount} руб.")
    
    print(f"📊 Создано платежей: {created_count}")
    return created_count

def main():
    """Основная функция создания данных"""
    print("🚀 Создание исправленных тестовых данных для Supabase\n")
    
    try:
        # Создаем данные в правильном порядке
        steps = [
            ("Способы оплаты", create_payment_methods),
            ("Тренеры", create_trainers),
            ("Сотрудники", create_staff_members),
            ("Родители", create_parents),
            ("Тренировочные группы", create_training_groups),
            ("Спортсмены", create_athletes),
            ("Тренировочные сессии", create_training_sessions),
            ("Платежи", create_payments),
        ]
        
        total_created = 0
        
        for step_name, step_func in steps:
            print(f"\n{'='*60}")
            print(f"ШАГ: {step_name}")
            print('='*60)
            
            try:
                created = step_func()
                total_created += created
            except Exception as e:
                print(f"❌ Ошибка в шаге {step_name}: {e}")
        
        # Итоговый отчет
        print(f"\n{'='*60}")
        print("ИТОГОВЫЙ ОТЧЕТ")
        print('='*60)
        
        from django.contrib.auth.models import User
        from core.models import Staff, Athlete, Parent, TrainingGroup, Payment, PaymentMethod, TrainingSession, Trainer
        
        print(f"📊 Финальная статистика:")
        print(f"  - Пользователей: {User.objects.count()}")
        print(f"  - Тренеров: {Trainer.objects.count()}")
        print(f"  - Сотрудников: {Staff.objects.count()}")
        print(f"  - Родителей: {Parent.objects.count()}")
        print(f"  - Спортсменов: {Athlete.objects.count()}")
        print(f"  - Групп: {TrainingGroup.objects.count()}")
        print(f"  - Способов оплаты: {PaymentMethod.objects.count()}")
        print(f"  - Тренировочных сессий: {TrainingSession.objects.count()}")
        print(f"  - Платежей: {Payment.objects.count()}")
        
        print(f"\n🎉 Создание данных завершено!")
        print(f"📈 Всего создано записей: {total_created}")
        print("✅ Supabase готов к полноценной работе!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()

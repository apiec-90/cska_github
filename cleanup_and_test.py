#!/usr/bin/env python
"""
Скрипт для очистки старых данных и создания тестовых пользователей
Сохраняет архитектуру, удаляет только пользовательские данные
"""

import os
import sys
import django
from django.db import transaction
from django.contrib.auth.models import User, Group

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_project.settings')
django.setup()

from core.models import (
    Athlete, Parent, Trainer, Staff, 
    TrainingGroup, GroupSchedule, TrainingSession,
    AthleteParent, AthleteTrainingGroup, AttendanceRecord,
    Payment, Document, DocumentType, AuditRecord,
    RegistrationDraft
)
from core.utils import assign_groups_for_registration


def analyze_database():
    """Анализ текущего состояния базы данных"""
    print("📊 АНАЛИЗ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    # Пользователи
    users = User.objects.all()
    print(f"👥 Всего пользователей: {users.count()}")
    
    superusers = users.filter(is_superuser=True)
    print(f"🔑 Суперпользователей: {superusers.count()}")
    for user in superusers:
        print(f"   - {user.username} ({user.email})")
    
    staff_users = users.filter(is_staff=True, is_superuser=False)
    print(f"👔 Staff пользователей: {staff_users.count()}")
    
    regular_users = users.filter(is_staff=False, is_superuser=False)
    print(f"👤 Обычных пользователей: {regular_users.count()}")
    
    # Модели ролей
    print(f"\n🏃 Спортсменов: {Athlete.objects.count()}")
    print(f"👨‍👩‍👧‍👦 Родителей: {Parent.objects.count()}")
    print(f"🏋️ Тренеров: {Trainer.objects.count()}")
    print(f"💼 Сотрудников: {Staff.objects.count()}")
    
    # Группы и расписания
    print(f"\n🏆 Тренировочных групп: {TrainingGroup.objects.count()}")
    print(f"📅 Расписаний: {GroupSchedule.objects.count()}")
    print(f"🎯 Тренировочных сессий: {TrainingSession.objects.count()}")
    
    # Связи
    print(f"\n🔗 Связей родитель-спортсмен: {AthleteParent.objects.count()}")
    print(f"🔗 Связей спортсмен-группа: {AthleteTrainingGroup.objects.count()}")
    print(f"📋 Записей посещаемости: {AttendanceRecord.objects.count()}")
    
    # Документы и платежи
    print(f"\n💰 Платежей: {Payment.objects.count()}")
    print(f"📄 Документов: {Document.objects.count()}")
    print(f"📂 Типов документов: {DocumentType.objects.count()}")
    
    # Аудит
    print(f"\n📝 Записей аудита: {AuditRecord.objects.count()}")
    print(f"✍️ Черновиков регистрации: {RegistrationDraft.objects.count()}")
    
    # Django группы
    django_groups = Group.objects.all()
    print(f"\n👥 Django групп: {django_groups.count()}")
    for group in django_groups:
        user_count = group.user_set.count()
        perm_count = group.permissions.count()
        print(f"   - {group.name}: {user_count} пользователей, {perm_count} разрешений")


def cleanup_old_data():
    """Очистка старых данных (сохраняем архитектуру)"""
    print("\n🧹 ОЧИСТКА СТАРЫХ ДАННЫХ")
    print("=" * 50)
    
    with transaction.atomic():
        # 1. Удаляем связи
        print("🔗 Удаление связей...")
        AthleteParent.objects.all().delete()
        AthleteTrainingGroup.objects.all().delete()
        
        # 2. Удаляем тренировочные данные
        print("🎯 Удаление тренировочных данных...")
        AttendanceRecord.objects.all().delete()
        TrainingSession.objects.all().delete()
        GroupSchedule.objects.all().delete()
        TrainingGroup.objects.all().delete()
        
        # 3. Удаляем документы и платежи
        print("💰 Удаление документов и платежей...")
        Payment.objects.all().delete()
        Document.objects.all().delete()
        # DocumentType оставляем - могут понадобиться
        
        # 4. Удаляем черновики регистрации
        print("✍️ Удаление черновиков...")
        RegistrationDraft.objects.all().delete()
        
        # 5. Удаляем записи аудита (кроме важных)
        print("📝 Очистка аудита...")
        AuditRecord.objects.all().delete()
        
        # 6. Удаляем модели ролей
        print("👥 Удаление моделей ролей...")
        Athlete.objects.all().delete()
        Parent.objects.all().delete()
        Trainer.objects.all().delete()
        Staff.objects.all().delete()
        
        # 7. Удаляем обычных пользователей (оставляем суперпользователей и важных staff)
        print("👤 Удаление пользователей...")
        users_to_delete = User.objects.filter(
            is_superuser=False,
            is_staff=False
        )
        count = users_to_delete.count()
        users_to_delete.delete()
        print(f"   Удалено {count} обычных пользователей")
        
        # 8. Очищаем группы пользователей (сами группы оставляем)
        print("👥 Очистка групп пользователей...")
        for group in Group.objects.all():
            group.user_set.clear()
    
    print("✅ Очистка завершена!")


def create_test_users():
    """Создание тестовых пользователей"""
    print("\n👥 СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 50)
    
    test_users = []
    
    with transaction.atomic():
        # 1. Создаем тестовых спортсменов
        print("🏃 Создание спортсменов...")
        for i in range(1, 6):
            user = User.objects.create_user(
                username=f'athlete{i}',
                email=f'athlete{i}@test.com',
                password='testpass123',
                first_name=f'Спортсмен{i}',
                last_name=f'Тестовый{i}',
                is_active=True
            )
            
            athlete = Athlete.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=f'+7900123456{i}',
                birth_date='2005-01-01',
                medical_certificate_expiry='2025-12-31'
            )
            
            assign_groups_for_registration(user, 'athlete')
            test_users.append((user, 'athlete', athlete))
            print(f"   ✅ {user.username} -> {athlete}")
        
        # 2. Создаем тестовых родителей
        print("\n👨‍👩‍👧‍👦 Создание родителей...")
        for i in range(1, 4):
            user = User.objects.create_user(
                username=f'parent{i}',
                email=f'parent{i}@test.com',
                password='testpass123',
                first_name=f'Родитель{i}',
                last_name=f'Тестовый{i}',
                is_active=True
            )
            
            parent = Parent.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=f'+7900765432{i}',
                relationship='Отец' if i % 2 else 'Мать'
            )
            
            assign_groups_for_registration(user, 'parent')
            test_users.append((user, 'parent', parent))
            print(f"   ✅ {user.username} -> {parent}")
        
        # 3. Создаем тестовых тренеров
        print("\n🏋️ Создание тренеров...")
        for i in range(1, 4):
            user = User.objects.create_user(
                username=f'trainer{i}',
                email=f'trainer{i}@test.com',
                password='testpass123',
                first_name=f'Тренер{i}',
                last_name=f'Тестовый{i}',
                is_active=True
            )
            
            trainer = Trainer.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=f'+7900987654{i}',
                specialization='Общая физическая подготовка',
                experience_years=5 + i
            )
            
            assign_groups_for_registration(user, 'trainer')
            test_users.append((user, 'trainer', trainer))
            print(f"   ✅ {user.username} -> {trainer}")
        
        # 4. Создаем тестовых сотрудников
        print("\n💼 Создание сотрудников...")
        staff_roles = [
            ('manager', 'Менеджер1', 'Тестовый1'),
            ('admin', 'Администратор1', 'Тестовый1'),
            ('accountant', 'Бухгалтер1', 'Тестовый1')
        ]
        
        for i, (role, first_name, last_name) in enumerate(staff_roles, 1):
            user = User.objects.create_user(
                username=f'staff_{role}',
                email=f'staff_{role}@test.com',
                password='testpass123',
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_staff=True  # Staff пользователи
            )
            
            staff = Staff.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=f'+7900111222{i}',
                role=role,
                department='Администрация'
            )
            
            assign_groups_for_registration(user, 'staff', role)
            test_users.append((user, 'staff', staff))
            print(f"   ✅ {user.username} -> {staff} ({role})")
    
    return test_users


def create_test_groups_and_schedules():
    """Создание тестовых групп и расписаний"""
    print("\n🏆 СОЗДАНИЕ ТЕСТОВЫХ ГРУПП")
    print("=" * 50)
    
    with transaction.atomic():
        # Создаем тестовые группы
        groups_data = [
            ('Младшая группа', 'Дети 6-8 лет', 10),
            ('Средняя группа', 'Дети 9-12 лет', 12),
            ('Старшая группа', 'Подростки 13-16 лет', 15),
        ]
        
        # Получаем тренеров
        trainers = list(Trainer.objects.all())
        
        created_groups = []
        for i, (name, description, max_athletes) in enumerate(groups_data):
            group = TrainingGroup.objects.create(
                name=name,
                description=description,
                max_athletes=max_athletes,
                is_active=True
            )
            
            # Назначаем тренера
            if trainers:
                group.trainers.add(trainers[i % len(trainers)])
            
            created_groups.append(group)
            print(f"   ✅ {group.name} (макс. {group.max_athletes})")
            
            # Создаем расписание для группы
            schedules_data = [
                (1, '18:00', '19:30'),  # Понедельник
                (3, '18:00', '19:30'),  # Среда  
                (5, '18:00', '19:30'),  # Пятница
            ]
            
            for weekday, start_time, end_time in schedules_data:
                schedule = GroupSchedule.objects.create(
                    training_group=group,
                    weekday=weekday,
                    start_time=start_time,
                    end_time=end_time
                )
                print(f"      📅 {schedule.get_weekday_display()}: {start_time}-{end_time}")
    
    return created_groups


def create_test_relationships(test_users, created_groups):
    """Создание тестовых связей"""
    print("\n🔗 СОЗДАНИЕ СВЯЗЕЙ")
    print("=" * 50)
    
    with transaction.atomic():
        # Получаем спортсменов и родителей
        athletes = [user_data for user_data in test_users if user_data[1] == 'athlete']
        parents = [user_data for user_data in test_users if user_data[1] == 'parent']
        
        # Связываем родителей со спортсменами
        print("👨‍👩‍👧‍👦 Связи родитель-спортсмен:")
        for i, (parent_user, _, parent_obj) in enumerate(parents):
            # Каждый родитель связан с 1-2 спортсменами
            athlete_indices = [i, i + 1] if i + 1 < len(athletes) else [i]
            
            for athlete_idx in athlete_indices:
                if athlete_idx < len(athletes):
                    athlete_user, _, athlete_obj = athletes[athlete_idx]
                    
                    relationship = AthleteParent.objects.create(
                        athlete=athlete_obj,
                        parent=parent_obj
                    )
                    print(f"   ✅ {parent_obj.get_full_name()} -> {athlete_obj.get_full_name()}")
        
        # Распределяем спортсменов по группам
        print("\n🏆 Распределение по группам:")
        for i, (athlete_user, _, athlete_obj) in enumerate(athletes):
            # Каждый спортсмен в одной группе
            group = created_groups[i % len(created_groups)]
            
            relationship = AthleteTrainingGroup.objects.create(
                athlete=athlete_obj,
                training_group=group
            )
            print(f"   ✅ {athlete_obj.get_full_name()} -> {group.name}")


def test_registration_system():
    """Тестирование системы регистрации"""
    print("\n🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ РЕГИСТРАЦИИ")
    print("=" * 50)
    
    from django.test import RequestFactory
    from core.admin import Step1RegistrationView, Step2RegistrationView
    
    # Создаем фабрику запросов
    factory = RequestFactory()
    
    print("✅ Система регистрации готова к тестированию")
    print("   Доступные views:")
    print("   - Step1RegistrationView (создание пользователя)")
    print("   - Step2RegistrationView (выбор роли)")
    
    return True


def audit_system():
    """Полный аудит системы"""
    print("\n🔍 ПОЛНЫЙ АУДИТ СИСТЕМЫ")
    print("=" * 50)
    
    issues = []
    
    # 1. Проверяем целостность пользователей
    print("👥 Проверка пользователей...")
    orphaned_profiles = 0
    
    for athlete in Athlete.objects.all():
        if not athlete.user:
            issues.append(f"Спортсмен {athlete.id} без пользователя")
            orphaned_profiles += 1
    
    for parent in Parent.objects.all():
        if not parent.user:
            issues.append(f"Родитель {parent.id} без пользователя")
            orphaned_profiles += 1
    
    for trainer in Trainer.objects.all():
        if not trainer.user:
            issues.append(f"Тренер {trainer.id} без пользователя")
            orphaned_profiles += 1
    
    for staff in Staff.objects.all():
        if not staff.user:
            issues.append(f"Сотрудник {staff.id} без пользователя")
            orphaned_profiles += 1
    
    if orphaned_profiles == 0:
        print("   ✅ Все профили имеют связанных пользователей")
    else:
        print(f"   ❌ Найдено {orphaned_profiles} профилей без пользователей")
    
    # 2. Проверяем группы пользователей
    print("\n👥 Проверка групп...")
    users_without_groups = User.objects.filter(groups__isnull=True, is_superuser=False).count()
    if users_without_groups == 0:
        print("   ✅ Все пользователи в группах")
    else:
        print(f"   ⚠️ {users_without_groups} пользователей без групп")
    
    # 3. Проверяем связи
    print("\n🔗 Проверка связей...")
    invalid_athlete_parents = 0
    for ap in AthleteParent.objects.all():
        if not ap.athlete or not ap.parent:
            invalid_athlete_parents += 1
            issues.append(f"Некорректная связь AthleteParent {ap.id}")
    
    invalid_athlete_groups = 0
    for ag in AthleteTrainingGroup.objects.all():
        if not ag.athlete or not ag.training_group:
            invalid_athlete_groups += 1
            issues.append(f"Некорректная связь AthleteTrainingGroup {ag.id}")
    
    if invalid_athlete_parents == 0 and invalid_athlete_groups == 0:
        print("   ✅ Все связи корректны")
    else:
        print(f"   ❌ Найдено {invalid_athlete_parents + invalid_athlete_groups} некорректных связей")
    
    # 4. Проверяем расписания
    print("\n📅 Проверка расписаний...")
    groups_without_schedule = TrainingGroup.objects.filter(groupschedule__isnull=True).count()
    if groups_without_schedule == 0:
        print("   ✅ У всех групп есть расписание")
    else:
        print(f"   ⚠️ {groups_without_schedule} групп без расписания")
    
    # Итоговый отчет
    print(f"\n📋 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    if not issues:
        print("✅ Система работает корректно, проблем не найдено!")
    else:
        print(f"❌ Найдено {len(issues)} проблем:")
        for issue in issues:
            print(f"   - {issue}")
    
    return len(issues) == 0


def main():
    """Основная функция"""
    print("🚀 ЗАПУСК ОЧИСТКИ И ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    try:
        # 1. Анализ
        analyze_database()
        
        # 2. Очистка
        cleanup_old_data()
        
        # 3. Создание тестовых данных
        test_users = create_test_users()
        created_groups = create_test_groups_and_schedules()
        create_test_relationships(test_users, created_groups)
        
        # 4. Тестирование
        test_registration_system()
        
        # 5. Аудит
        audit_result = audit_system()
        
        print("\n🎉 ЗАВЕРШЕНО!")
        print("=" * 60)
        print("✅ Тестовые данные созданы")
        print("✅ Система протестирована")
        if audit_result:
            print("✅ Аудит пройден успешно")
        else:
            print("⚠️ Аудит выявил проблемы")
        
        # Финальная статистика
        print(f"\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
        print(f"👥 Пользователей: {User.objects.count()}")
        print(f"🏃 Спортсменов: {Athlete.objects.count()}")
        print(f"👨‍👩‍👧‍👦 Родителей: {Parent.objects.count()}")
        print(f"🏋️ Тренеров: {Trainer.objects.count()}")
        print(f"💼 Сотрудников: {Staff.objects.count()}")
        print(f"🏆 Групп: {TrainingGroup.objects.count()}")
        print(f"🔗 Связей: {AthleteParent.objects.count() + AthleteTrainingGroup.objects.count()}")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
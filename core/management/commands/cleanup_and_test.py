from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User, Group
 
import os

from core.models import (
    Athlete, Parent, Trainer, Staff, 
    TrainingGroup, GroupSchedule, TrainingSession,
    AthleteParent, AthleteTrainingGroup, AttendanceRecord,
    Payment, Document, DocumentType, AuditRecord,
    RegistrationDraft
)

class Command(BaseCommand):
    help = 'Cleanup old data and create test users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='Only analyze current state without changes',
        )

    def assign_groups_for_registration(self, user, role, subrole=None):
        """Local implementation of group assignment"""
        user.groups.clear()
        
        role_to_group = {
            'trainer': 'Тренеры',
            'athlete': 'Спортсмены', 
            'parent': 'Родители',
            'staff': 'Сотрудники',
        }
        
        if role in role_to_group:
            group_name = role_to_group[role]
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        
        if role == 'staff' and subrole:
            subrole_to_group = {
                'manager': 'Менеджеры',
            }
            if subrole in subrole_to_group:
                subrole_group_name = subrole_to_group[subrole]
                subrole_group, created = Group.objects.get_or_create(name=subrole_group_name)
                user.groups.add(subrole_group)

    def handle(self, *args, **options):
        if options['analyze_only']:
            self.analyze_database()
        else:
            self.full_cleanup_and_test()

    def analyze_database(self):
        """Анализ текущего состояния базы данных"""
        self.stdout.write("📊 АНАЛИЗ БАЗЫ ДАННЫХ")
        self.stdout.write("=" * 50)
        
        # Пользователи
        users = User.objects.all()
        self.stdout.write(f"👥 Всего пользователей: {users.count()}")
        
        superusers = users.filter(is_superuser=True)
        self.stdout.write(f"🔑 Суперпользователей: {superusers.count()}")
        for user in superusers:
            self.stdout.write(f"   - {user.username} ({user.email})")
        
        staff_users = users.filter(is_staff=True, is_superuser=False)
        self.stdout.write(f"👔 Staff пользователей: {staff_users.count()}")
        
        regular_users = users.filter(is_staff=False, is_superuser=False)
        self.stdout.write(f"👤 Обычных пользователей: {regular_users.count()}")
        
        # Модели ролей
        self.stdout.write(f"\n🏃 Спортсменов: {Athlete.objects.count()}")
        self.stdout.write(f"👨‍👩‍👧‍👦 Родителей: {Parent.objects.count()}")
        self.stdout.write(f"🏋️ Тренеров: {Trainer.objects.count()}")
        self.stdout.write(f"💼 Сотрудников: {Staff.objects.count()}")
        
        # Группы и расписания
        self.stdout.write(f"\n🏆 Тренировочных групп: {TrainingGroup.objects.count()}")
        self.stdout.write(f"📅 Расписаний: {GroupSchedule.objects.count()}")
        self.stdout.write(f"🎯 Тренировочных сессий: {TrainingSession.objects.count()}")
        
        # Связи
        self.stdout.write(f"\n🔗 Связей родитель-спортсмен: {AthleteParent.objects.count()}")
        self.stdout.write(f"🔗 Связей спортсмен-группа: {AthleteTrainingGroup.objects.count()}")
        self.stdout.write(f"📋 Записей посещаемости: {AttendanceRecord.objects.count()}")
        
        # Документы и платежи
        self.stdout.write(f"\n💰 Платежей: {Payment.objects.count()}")
        self.stdout.write(f"📄 Документов: {Document.objects.count()}")
        self.stdout.write(f"📂 Типов документов: {DocumentType.objects.count()}")
        
        # Аудит
        self.stdout.write(f"\n📝 Записей аудита: {AuditRecord.objects.count()}")
        self.stdout.write(f"✍️ Черновиков регистрации: {RegistrationDraft.objects.count()}")
        
        # Django группы
        django_groups = Group.objects.all()
        self.stdout.write(f"\n👥 Django групп: {django_groups.count()}")
        for group in django_groups:
            user_count = group.user_set.count()
            perm_count = group.permissions.count()
            self.stdout.write(f"   - {group.name}: {user_count} пользователей, {perm_count} разрешений")

    def cleanup_old_data(self):
        """Очистка старых данных (сохраняем архитектуру)"""
        self.stdout.write("\n🧹 ОЧИСТКА СТАРЫХ ДАННЫХ")
        self.stdout.write("=" * 50)
        
        with transaction.atomic():
            # 1. Удаляем связи
            self.stdout.write("🔗 Удаление связей...")
            AthleteParent.objects.all().delete()
            AthleteTrainingGroup.objects.all().delete()
            
            # 2. Удаляем тренировочные данные
            self.stdout.write("🎯 Удаление тренировочных данных...")
            AttendanceRecord.objects.all().delete()
            TrainingSession.objects.all().delete()
            GroupSchedule.objects.all().delete()
            TrainingGroup.objects.all().delete()
            
            # 3. Удаляем документы и платежи
            self.stdout.write("💰 Удаление документов и платежей...")
            Payment.objects.all().delete()
            Document.objects.all().delete()
            
            # 4. Удаляем черновики регистрации
            self.stdout.write("✍️ Удаление черновиков...")
            RegistrationDraft.objects.all().delete()
            
            # 5. Удаляем записи аудита
            self.stdout.write("📝 Очистка аудита...")
            AuditRecord.objects.all().delete()
            
            # 6. Удаляем модели ролей
            self.stdout.write("👥 Удаление моделей ролей...")
            Athlete.objects.all().delete()
            Parent.objects.all().delete()
            Trainer.objects.all().delete()
            Staff.objects.all().delete()
            
            # 7. Удаляем обычных пользователей (оставляем суперпользователей)
            self.stdout.write("👤 Удаление пользователей...")
            users_to_delete = User.objects.filter(
                is_superuser=False
            )
            count = users_to_delete.count()
            users_to_delete.delete()
            self.stdout.write(f"   Удалено {count} пользователей")
            
            # 8. Очищаем группы пользователей (сами группы оставляем)
            self.stdout.write("👥 Очистка групп пользователей...")
            for group in Group.objects.all():
                group.user_set.clear()
        
        self.stdout.write(self.style.SUCCESS("✅ Очистка завершена!"))

    def create_test_users(self):
        """Создание тестовых пользователей"""
        self.stdout.write("\n👥 СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ")
        self.stdout.write("=" * 50)
        
        test_users = []
        
        with transaction.atomic():
            # 1. Создаем тестовых спортсменов
            self.stdout.write("🏃 Создание спортсменов...")
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
                    birth_date='2005-01-01'
                )
                
                self.assign_groups_for_registration(user, 'athlete')
                test_users.append((user, 'athlete', athlete))
                self.stdout.write(f"   ✅ {user.username}")
            
            # 2. Создаем тестовых родителей
            self.stdout.write("\n👨‍👩‍👧‍👦 Создание родителей...")
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
                    phone=f'+7900765432{i}'
                )
                
                self.assign_groups_for_registration(user, 'parent')
                test_users.append((user, 'parent', parent))
                self.stdout.write(f"   ✅ {user.username}")
            
            # 3. Создаем тестовых тренеров
            self.stdout.write("\n🏋️ Создание тренеров...")
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
                    birth_date='1985-01-01'
                )
                
                self.assign_groups_for_registration(user, 'trainer')
                test_users.append((user, 'trainer', trainer))
                self.stdout.write(f"   ✅ {user.username}")
            
            # 4. Создаем тестовых сотрудников
            self.stdout.write("\n💼 Создание сотрудников...")
            staff_roles = [
                ('manager', 'Менеджер1', 'Тестовый1')
            ]
            
            for i, (role, first_name, last_name) in enumerate(staff_roles, 1):
                user = User.objects.create_user(
                    username=f'staff_{role}',
                    email=f'staff_{role}@test.com',
                    password='testpass123',
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    is_staff=True
                )
                
                staff = Staff.objects.create(
                    user=user,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    phone=f'+7900111222{i}',
                    birth_date='1980-01-01',
                    role=role
                )
                
                self.assign_groups_for_registration(user, 'staff', role)
                test_users.append((user, 'staff', staff))
                self.stdout.write(f"   ✅ {user.username} ({role})")
        
        return test_users

    def create_test_groups_and_schedules(self):
        """Создание тестовых групп и расписаний"""
        self.stdout.write("\n🏆 СОЗДАНИЕ ТЕСТОВЫХ ГРУПП")
        self.stdout.write("=" * 50)
        
        with transaction.atomic():
            groups_data = [
                ('Младшая группа', 6, 8, 10),
                ('Средняя группа', 9, 12, 12),
                ('Старшая группа', 13, 16, 15),
            ]
            
            trainers = list(Trainer.objects.all())
            created_groups = []
            
            for i, (name, age_min, age_max, max_athletes) in enumerate(groups_data):
                group = TrainingGroup.objects.create(
                    name=name,
                    age_min=age_min,
                    age_max=age_max,
                    max_athletes=max_athletes,
                    is_active=True
                )
                
                if trainers:
                    group.trainer = trainers[i % len(trainers)]
                    group.save()
                
                created_groups.append(group)
                self.stdout.write(f"   ✅ {group.name}")
                
                # Создаем расписание
                schedules_data = [
                    (1, '18:00', '19:30'),  # Понедельник
                    (3, '18:00', '19:30'),  # Среда  
                    (5, '18:00', '19:30'),  # Пятница
                ]
                
                for weekday, start_time, end_time in schedules_data:
                    GroupSchedule.objects.create(
                        training_group=group,
                        weekday=weekday,
                        start_time=start_time,
                        end_time=end_time
                    )
        
        return created_groups

    def create_test_relationships(self, test_users, created_groups):
        """Создание тестовых связей"""
        self.stdout.write("\n🔗 СОЗДАНИЕ СВЯЗЕЙ")
        self.stdout.write("=" * 50)
        
        with transaction.atomic():
            athletes = [user_data for user_data in test_users if user_data[1] == 'athlete']
            parents = [user_data for user_data in test_users if user_data[1] == 'parent']
            
            # Связываем родителей со спортсменами
            self.stdout.write("👨‍👩‍👧‍👦 Связи родитель-спортсмен:")
            for i, (parent_user, _, parent_obj) in enumerate(parents):
                athlete_indices = [i, i + 1] if i + 1 < len(athletes) else [i]
                
                for athlete_idx in athlete_indices:
                    if athlete_idx < len(athletes):
                        athlete_user, _, athlete_obj = athletes[athlete_idx]
                        
                        AthleteParent.objects.create(
                            athlete=athlete_obj,
                            parent=parent_obj
                        )
                        self.stdout.write(f"   ✅ {parent_obj} -> {athlete_obj}")
            
            # Распределяем спортсменов по группам
            self.stdout.write("\n🏆 Распределение по группам:")
            for i, (athlete_user, _, athlete_obj) in enumerate(athletes):
                group = created_groups[i % len(created_groups)]
                
                AthleteTrainingGroup.objects.create(
                    athlete=athlete_obj,
                    training_group=group
                )
                self.stdout.write(f"   ✅ {athlete_obj} -> {group.name}")

    def audit_system(self):
        """Полный аудит системы"""
        self.stdout.write("\n🔍 ПОЛНЫЙ АУДИТ СИСТЕМЫ")
        self.stdout.write("=" * 50)
        
        issues = []
        
        # 1. Проверяем целостность пользователей
        self.stdout.write("👥 Проверка пользователей...")
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
            self.stdout.write("   ✅ Все профили имеют связанных пользователей")
        else:
            self.stdout.write(f"   ❌ Найдено {orphaned_profiles} профилей без пользователей")
        
        # 2. Проверяем группы пользователей
        self.stdout.write("\n👥 Проверка групп...")
        users_without_groups = User.objects.filter(groups__isnull=True, is_superuser=False).count()
        if users_without_groups == 0:
            self.stdout.write("   ✅ Все пользователи в группах")
        else:
            self.stdout.write(f"   ⚠️ {users_without_groups} пользователей без групп")
        
        # 3. Проверяем связи
        self.stdout.write("\n🔗 Проверка связей...")
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
            self.stdout.write("   ✅ Все связи корректны")
        else:
            self.stdout.write(f"   ❌ Найдено {invalid_athlete_parents + invalid_athlete_groups} некорректных связей")
        
        # 4. Проверяем расписания
        self.stdout.write("\n📅 Проверка расписаний...")
        groups_without_schedule = TrainingGroup.objects.filter(groupschedule__isnull=True).count()
        if groups_without_schedule == 0:
            self.stdout.write("   ✅ У всех групп есть расписание")
        else:
            self.stdout.write(f"   ⚠️ {groups_without_schedule} групп без расписания")
        
        # Итоговый отчет
        self.stdout.write("\n📋 ИТОГОВЫЙ ОТЧЕТ")
        self.stdout.write("=" * 50)
        if not issues:
            self.stdout.write(self.style.SUCCESS("✅ Система работает корректно, проблем не найдено!"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Найдено {len(issues)} проблем:"))
            for issue in issues:
                self.stdout.write(f"   - {issue}")
        
        return len(issues) == 0

    def full_cleanup_and_test(self):
        """Полная очистка и тестирование"""
        self.stdout.write(self.style.SUCCESS("🚀 ЗАПУСК ОЧИСТКИ И ТЕСТИРОВАНИЯ"))
        self.stdout.write("=" * 60)
        
        # Временно отключаем сигналы
        os.environ['DISABLE_SIGNALS'] = '1'
        
        try:
            # 1. Анализ
            self.analyze_database()
            
            # 2. Очистка
            self.cleanup_old_data()
            
            # 3. Создание тестовых данных
            test_users = self.create_test_users()
            created_groups = self.create_test_groups_and_schedules()
            self.create_test_relationships(test_users, created_groups)
            
            # 4. Аудит
            audit_result = self.audit_system()
            
            self.stdout.write("\n🎉 ЗАВЕРШЕНО!")
            self.stdout.write("=" * 60)
            self.stdout.write(self.style.SUCCESS("✅ Тестовые данные созданы"))
            self.stdout.write(self.style.SUCCESS("✅ Система протестирована"))
            if audit_result:
                self.stdout.write(self.style.SUCCESS("✅ Аудит пройден успешно"))
            else:
                self.stdout.write(self.style.WARNING("⚠️ Аудит выявил проблемы"))
            
            # Финальная статистика
            self.stdout.write("\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
            self.stdout.write(f"👥 Пользователей: {User.objects.count()}")
            self.stdout.write(f"🏃 Спортсменов: {Athlete.objects.count()}")
            self.stdout.write(f"👨‍👩‍👧‍👦 Родителей: {Parent.objects.count()}")
            self.stdout.write(f"🏋️ Тренеров: {Trainer.objects.count()}")
            self.stdout.write(f"💼 Сотрудников: {Staff.objects.count()}")
            self.stdout.write(f"🏆 Групп: {TrainingGroup.objects.count()}")
            self.stdout.write(f"🔗 Связей: {AthleteParent.objects.count() + AthleteTrainingGroup.objects.count()}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ ОШИБКА: {e}"))
            import traceback
            traceback.print_exc()
        finally:
            # Включаем сигналы обратно
            if 'DISABLE_SIGNALS' in os.environ:
                del os.environ['DISABLE_SIGNALS']
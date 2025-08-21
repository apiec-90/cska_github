from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from datetime import datetime, timedelta
import random

from core.models import (
    Staff, Trainer, Athlete, Parent, TrainingGroup, 
    AthleteTrainingGroup, AthleteParent, GroupSchedule,
    TrainingSession, AttendanceRecord
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает тестовые данные для системы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие тестовые данные',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_test_data()
            
        self.create_test_data()
        self.stdout.write(
            self.style.SUCCESS('Тестовые данные успешно созданы!')
        )

    def clear_test_data(self):
        """Очистка тестовых данных"""
        self.stdout.write('Очистка существующих тестовых данных...')
        
        # Удаляем записи посещаемости
        AttendanceRecord.objects.filter(
            session__training_group__name__startswith='Тест'
        ).delete()
        
        # Удаляем сессии
        TrainingSession.objects.filter(
            training_group__name__startswith='Тест'
        ).delete()
        
        # Удаляем связи
        AthleteTrainingGroup.objects.filter(
            training_group__name__startswith='Тест'
        ).delete()
        AthleteParent.objects.filter(
            athlete__user__username__startswith='test_'
        ).delete()
        
        # Удаляем расписание
        GroupSchedule.objects.filter(
            training_group__name__startswith='Тест'
        ).delete()
        
        # Удаляем группы
        TrainingGroup.objects.filter(name__startswith='Тест').delete()
        
        # Удаляем профили
        Athlete.objects.filter(user__username__startswith='test_').delete()
        Parent.objects.filter(user__username__startswith='test_').delete()
        Trainer.objects.filter(user__username__startswith='test_').delete()
        Staff.objects.filter(user__username__startswith='test_').delete()
        
        # Удаляем пользователей
        User.objects.filter(username__startswith='test_').delete()

    def create_test_data(self):
        """Создание тестовых данных"""
        self.stdout.write('Создание тестовых данных...')
        
        # Создаем тренеров
        trainers = self.create_trainers()
        
        # Создаем родителей
        parents = self.create_parents()
        
        # Создаем спортсменов
        athletes = self.create_athletes()
        
        # Создаем связи родители-дети
        self.create_parent_athlete_relations(parents, athletes)
        
        # Создаем тренировочные группы
        groups = self.create_training_groups(trainers)
        
        # Добавляем спортсменов в группы
        self.assign_athletes_to_groups(athletes, groups)
        
        # Создаем расписание
        self.create_schedules(groups)
        
        # Создаем тренировочные сессии
        self.create_training_sessions(groups)
        
        # Создаем записи посещаемости
        self.create_attendance_records(groups)

    def create_trainers(self):
        """Создание тестовых тренеров"""
        self.stdout.write('  Создание тренеров...')
        
        trainers_data = [
            ('Иван', 'Петров', 'ivan.petrov'),
            ('Мария', 'Сидорова', 'maria.sidorova'),
            ('Алексей', 'Козлов', 'alexey.kozlov'),
        ]
        
        trainers = []
        for first_name, last_name, username in trainers_data:
            # Создаем пользователя
            user = User.objects.create_user(
                username=f'test_{username}',
                email=f'{username}@test.com',
                password='test123',
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Добавляем в группу тренеров
            trainer_group, _ = Group.objects.get_or_create(name='Тренеры')
            user.groups.add(trainer_group)
            
            # Создаем профиль тренера
            trainer = Trainer.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone=f'+7 (999) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                birth_date=datetime(1980 + random.randint(0, 15), random.randint(1, 12), random.randint(1, 28)).date()
            )
            trainers.append(trainer)
            
        self.stdout.write(f'    Создано {len(trainers)} тренеров')
        return trainers

    def create_parents(self):
        """Создание тестовых родителей"""
        self.stdout.write('  Создание родителей...')
        
        parents_data = [
            ('Елена', 'Иванова', 'elena.ivanova'),
            ('Сергей', 'Смирнов', 'sergey.smirnov'),
            ('Ольга', 'Попова', 'olga.popova'),
            ('Дмитрий', 'Волков', 'dmitriy.volkov'),
            ('Анна', 'Морозова', 'anna.morozova'),
        ]
        
        parents = []
        for first_name, last_name, username in parents_data:
            user = User.objects.create_user(
                username=f'test_{username}',
                email=f'{username}@test.com',
                password='test123',
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Добавляем в группу родителей
            parent_group, _ = Group.objects.get_or_create(name='Родители')
            user.groups.add(parent_group)
            
            parent = Parent.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone=f'+7 (999) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                birth_date=datetime(1975 + random.randint(0, 20), random.randint(1, 12), random.randint(1, 28)).date()
            )
            parents.append(parent)
            
        self.stdout.write(f'    Создано {len(parents)} родителей')
        return parents

    def create_athletes(self):
        """Создание тестовых спортсменов"""
        self.stdout.write('  Создание спортсменов...')
        
        athletes_data = [
            ('Максим', 'Иванов', 'maxim.ivanov', 2010),
            ('София', 'Смирнова', 'sofia.smirnova', 2011),
            ('Артём', 'Попов', 'artem.popov', 2012),
            ('Полина', 'Волкова', 'polina.volkova', 2009),
            ('Никита', 'Морозов', 'nikita.morozov', 2013),
            ('Алиса', 'Петрова', 'alisa.petrova', 2010),
            ('Егор', 'Сидоров', 'egor.sidorov', 2011),
            ('Варвара', 'Козлова', 'varvara.kozlova', 2012),
        ]
        
        athletes = []
        for first_name, last_name, username, birth_year in athletes_data:
            user = User.objects.create_user(
                username=f'test_{username}',
                email=f'{username}@test.com',
                password='test123',
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Добавляем в группу спортсменов
            athlete_group, _ = Group.objects.get_or_create(name='Спортсмены')
            user.groups.add(athlete_group)
            
            athlete = Athlete.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone=f'+7 (999) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                birth_date=datetime(birth_year, random.randint(1, 12), random.randint(1, 28)).date()
            )
            athletes.append(athlete)
            
        self.stdout.write(f'    Создано {len(athletes)} спортсменов')
        return athletes

    def create_parent_athlete_relations(self, parents, athletes):
        """Создание связей родители-дети"""
        self.stdout.write('  Создание связей родители-дети...')
        
        relations_count = 0
        for i, athlete in enumerate(athletes):
            # Каждому ребенку назначаем 1-2 родителей
            parent_count = random.randint(1, min(2, len(parents)))
            selected_parents = random.sample(parents, parent_count)
            
            for parent in selected_parents:
                AthleteParent.objects.get_or_create(
                    athlete=athlete,
                    parent=parent
                )
                relations_count += 1
                
        self.stdout.write(f'    Создано {relations_count} связей родитель-ребенок')

    def create_training_groups(self, trainers):
        """Создание тренировочных групп"""
        self.stdout.write('  Создание тренировочных групп...')
        
        groups_data = [
            ('Тест - Младшая группа (6-8 лет)', 6, 8),
            ('Тест - Средняя группа (9-12 лет)', 9, 12),
            ('Тест - Старшая группа (13-16 лет)', 13, 16),
        ]
        
        groups = []
        for i, (name, age_min, age_max) in enumerate(groups_data):
            trainer = trainers[i % len(trainers)]  # Распределяем тренеров
            
            group = TrainingGroup.objects.create(
                name=name,
                age_min=age_min,
                age_max=age_max,
                trainer=trainer,
                max_athletes=15,
                is_active=True
            )
            groups.append(group)
            
        self.stdout.write(f'    Создано {len(groups)} тренировочных групп')
        return groups

    def assign_athletes_to_groups(self, athletes, groups):
        """Назначение спортсменов в группы"""
        self.stdout.write('  Назначение спортсменов в группы...')
        
        assignments = 0
        for athlete in athletes:
            # Определяем группу по возрасту
            age = (timezone.now().date() - athlete.birth_date).days // 365
            
            if age <= 8:
                group = groups[0]  # Младшая
            elif age <= 12:
                group = groups[1]  # Средняя
            else:
                group = groups[2]  # Старшая
                
            AthleteTrainingGroup.objects.get_or_create(
                athlete=athlete,
                training_group=group
            )
            assignments += 1
            
        self.stdout.write(f'    Создано {assignments} назначений в группы')

    def create_schedules(self, groups):
        """Создание расписания групп"""
        self.stdout.write('  Создание расписания...')
        
        schedules_data = [
            (1, '16:00', '17:30'),  # Понедельник
            (3, '16:00', '17:30'),  # Среда  
            (5, '16:00', '17:30'),  # Пятница
        ]
        
        schedule_count = 0
        for group in groups:
            for weekday, start_time, end_time in schedules_data:
                GroupSchedule.objects.get_or_create(
                    training_group=group,
                    weekday=weekday,
                    start_time=start_time,
                    end_time=end_time
                )
                schedule_count += 1
                
        self.stdout.write(f'    Создано {schedule_count} записей расписания')

    def create_training_sessions(self, groups):
        """Создание тренировочных сессий"""
        self.stdout.write('  Создание тренировочных сессий...')
        
        sessions = []
        today = timezone.now().date()
        
        # Создаем сессии на последние 2 недели и следующую неделю
        for days_offset in range(-14, 8):
            date = today + timedelta(days=days_offset)
            weekday = date.weekday() + 1  # Django использует 1-7
            
            for group in groups:
                # Проверяем, есть ли расписание на этот день
                schedule = GroupSchedule.objects.filter(
                    training_group=group,
                    weekday=weekday
                ).first()
                
                if schedule:
                    session = TrainingSession.objects.get_or_create(
                        training_group=group,
                        date=date,
                        start_time=schedule.start_time,
                        defaults={
                            'end_time': schedule.end_time,
                            'is_closed': date < today,  # Прошедшие сессии закрыты
                            'is_canceled': False
                        }
                    )[0]
                    sessions.append(session)
                    
        self.stdout.write(f'    Создано {len(sessions)} тренировочных сессий')
        return sessions

    def create_attendance_records(self, groups):
        """Создание записей посещаемости"""
        self.stdout.write('  Создание записей посещаемости...')
        
        records_count = 0
        today = timezone.now().date()
        
        # Создаем записи только для прошедших сессий
        past_sessions = TrainingSession.objects.filter(
            training_group__in=groups,
            date__lt=today,
            is_closed=True
        )
        
        # Получаем админа как того, кто отмечал посещаемость
        admin_staff = Staff.objects.filter(user__is_superuser=True).first()
        if not admin_staff:
            # Создаем staff для admin пользователя
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                admin_staff = Staff.objects.create(
                    user=admin_user,
                    first_name=admin_user.first_name or 'Admin',
                    last_name=admin_user.last_name or 'User',
                    phone='+7 (999) 999-99-99',
                    birth_date=datetime(1990, 1, 1).date(),
                    subrole='manager'
                )
        
        for session in past_sessions:
            # Получаем всех спортсменов группы
            athletes = Athlete.objects.filter(
                athletetraininggroup__training_group=session.training_group
            )
            
            for athlete in athletes:
                # 85% вероятность присутствия
                was_present = random.random() < 0.85
                
                AttendanceRecord.objects.get_or_create(
                    athlete=athlete,
                    session=session,
                    defaults={
                        'was_present': was_present,
                        'marked_by': admin_staff
                    }
                )
                records_count += 1
                
        self.stdout.write(f'    Создано {records_count} записей посещаемости')

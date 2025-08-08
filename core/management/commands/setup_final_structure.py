from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Staff, Parent, Athlete, Trainer, TrainingGroup, AthleteTrainingGroup, AthleteParent
from datetime import date
import os

class Command(BaseCommand):
    help = 'Настройка новой структуры БД с группами и пользователями (финальная)'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем настройку новой структуры...')
        
        # Временно отключаем сигналы
        from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
        from django.dispatch import receiver
        
        # Отключаем все сигналы
        post_save.receivers = []
        post_delete.receivers = []
        pre_save.receivers = []
        m2m_changed.receivers = []
        
        # Очищаем существующие данные
        self.stdout.write('Очищаем существующие данные...')
        AthleteTrainingGroup.objects.all().delete()
        AthleteParent.objects.all().delete()
        TrainingGroup.objects.all().delete()
        Trainer.objects.all().delete()
        Parent.objects.all().delete()
        Athlete.objects.all().delete()
        Staff.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        
        # Создаем основные группы
        self.stdout.write('Создаем группы...')
        trainers_group = Group.objects.create(name='Тренеры')
        parents_group = Group.objects.create(name='Родители')
        athletes_group = Group.objects.create(name='Спортсмены')
        managers_group = Group.objects.create(name='Менеджеры')
        
        # Создаем пользователей и связываем с группами
        self.stdout.write('Создаем пользователей...')
        
        # Создаем менеджера
        manager_user = User.objects.create_user(
            username='manager1',
            email='manager@example.com',
            password='password123',
            first_name='Иван',
            last_name='Менеджеров'
        )
        
        # Создаем менеджера в Staff
        manager_staff = Staff.objects.create(
            user=manager_user,
            role='manager',
            phone='+79001234567',
            birth_date=date(1985, 5, 15)
        )
        
        # Добавляем в группу после создания Staff
        manager_user.groups.add(managers_group)
        
        # Создаем тренеров
        trainers_data = [
            {'username': 'trainer1', 'first_name': 'Алексей', 'last_name': 'Тренеров'},
            {'username': 'trainer2', 'first_name': 'Мария', 'last_name': 'Тренерова'},
        ]
        
        trainers = []
        for i, trainer_data in enumerate(trainers_data):
            user = User.objects.create_user(
                username=trainer_data['username'],
                email=f'{trainer_data["username"]}@example.com',
                password='password123',
                first_name=trainer_data['first_name'],
                last_name=trainer_data['last_name']
            )
            
            trainer = Trainer.objects.create(
                user=user,
                phone=f'+7900123456{i+1}',
                birth_date=date(1990, 3, 10 + i)
            )
            trainers.append(trainer)
            
            # Добавляем в группу после создания Trainer
            user.groups.add(trainers_group)
        
        # Создаем родителей
        parents_data = [
            {'username': 'parent1', 'first_name': 'Ольга', 'last_name': 'Иванова'},
            {'username': 'parent2', 'first_name': 'Сергей', 'last_name': 'Петров'},
            {'username': 'parent3', 'first_name': 'Елена', 'last_name': 'Сидорова'},
            {'username': 'parent4', 'first_name': 'Дмитрий', 'last_name': 'Козлов'},
            {'username': 'parent5', 'first_name': 'Анна', 'last_name': 'Смирнова'},
            {'username': 'parent6', 'first_name': 'Владимир', 'last_name': 'Попов'},
            {'username': 'parent7', 'first_name': 'Татьяна', 'last_name': 'Соколова'},
            {'username': 'parent8', 'first_name': 'Андрей', 'last_name': 'Лебедев'},
        ]
        
        parents = []
        for i, parent_data in enumerate(parents_data):
            user = User.objects.create_user(
                username=parent_data['username'],
                email=f'{parent_data["username"]}@example.com',
                password='password123',
                first_name=parent_data['first_name'],
                last_name=parent_data['last_name']
            )
            
            parent = Parent.objects.create(user=user)
            parents.append(parent)
            
            # Добавляем в группу после создания Parent
            user.groups.add(parents_group)
        
        # Создаем спортсменов
        athletes_data = [
            {'username': 'athlete1', 'first_name': 'Михаил', 'last_name': 'Иванов', 'birth_date': date(2010, 1, 15)},
            {'username': 'athlete2', 'first_name': 'Анна', 'last_name': 'Петрова', 'birth_date': date(2011, 3, 20)},
            {'username': 'athlete3', 'first_name': 'Денис', 'last_name': 'Сидоров', 'birth_date': date(2010, 7, 8)},
            {'username': 'athlete4', 'first_name': 'Ксения', 'last_name': 'Козлова', 'birth_date': date(2011, 11, 12)},
            {'username': 'athlete5', 'first_name': 'Артем', 'last_name': 'Смирнов', 'birth_date': date(2010, 5, 25)},
            {'username': 'athlete6', 'first_name': 'София', 'last_name': 'Попова', 'birth_date': date(2011, 9, 3)},
            {'username': 'athlete7', 'first_name': 'Игорь', 'last_name': 'Соколов', 'birth_date': date(2010, 12, 18)},
            {'username': 'athlete8', 'first_name': 'Виктория', 'last_name': 'Лебедева', 'birth_date': date(2011, 2, 7)},
        ]
        
        athletes = []
        for i, athlete_data in enumerate(athletes_data):
            user = User.objects.create_user(
                username=athlete_data['username'],
                email=f'{athlete_data["username"]}@example.com',
                password='password123',
                first_name=athlete_data['first_name'],
                last_name=athlete_data['last_name']
            )
            
            athlete = Athlete.objects.create(
                user=user,
                birth_date=athlete_data['birth_date']
            )
            athletes.append(athlete)
            
            # Добавляем в группу после создания Athlete
            user.groups.add(athletes_group)
        
        # Создаем тренировочные группы
        self.stdout.write('Создаем тренировочные группы...')
        groups_data = [
            {'name': 'Футбольная группа А', 'age_min': 10, 'age_max': 12, 'trainer': trainers[0]},
            {'name': 'Футбольная группа Б', 'age_min': 10, 'age_max': 12, 'trainer': trainers[0]},
            {'name': 'Баскетбольная группа А', 'age_min': 10, 'age_max': 12, 'trainer': trainers[1]},
            {'name': 'Баскетбольная группа Б', 'age_min': 10, 'age_max': 12, 'trainer': trainers[1]},
            {'name': 'Смешанная группа', 'age_min': 10, 'age_max': 12, 'trainer': trainers[0]},
        ]
        
        training_groups = []
        for group_data in groups_data:
            group = TrainingGroup.objects.create(
                name=group_data['name'],
                age_min=group_data['age_min'],
                age_max=group_data['age_max'],
                trainer=group_data['trainer']
            )
            training_groups.append(group)
        
        # Распределяем спортсменов по группам (по 4 в каждую группу)
        self.stdout.write('Распределяем спортсменов по группам...')
        for i, athlete in enumerate(athletes):
            group_index = i // 4  # По 4 спортсмена в группу
            if group_index < len(training_groups):
                AthleteTrainingGroup.objects.create(
                    athlete=athlete,
                    training_group=training_groups[group_index]
                )
        
        # Связываем спортсменов с родителями
        self.stdout.write('Связываем спортсменов с родителями...')
        for i, athlete in enumerate(athletes):
            parent_index = i // 2  # По 2 спортсмена на родителя
            if parent_index < len(parents):
                AthleteParent.objects.create(
                    athlete=athlete,
                    parent=parents[parent_index]
                )
        
        self.stdout.write(self.style.SUCCESS('Структура успешно создана!'))
        self.stdout.write(f'Создано:')
        self.stdout.write(f'- {User.objects.count()} пользователей')
        self.stdout.write(f'- {Group.objects.count()} групп')
        self.stdout.write(f'- {Trainer.objects.count()} тренеров')
        self.stdout.write(f'- {Parent.objects.count()} родителей')
        self.stdout.write(f'- {Athlete.objects.count()} спортсменов')
        self.stdout.write(f'- {TrainingGroup.objects.count()} тренировочных групп')
        self.stdout.write(f'- {AthleteTrainingGroup.objects.count()} связей спортсмен-группа')
        self.stdout.write(f'- {AthleteParent.objects.count()} связей спортсмен-родитель')

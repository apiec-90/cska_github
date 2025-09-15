from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date, time

from core.models import (
    Athlete, Parent, Trainer, Staff,
    TrainingGroup, AthleteTrainingGroup, AthleteParent, GroupSchedule,
)


class Command(BaseCommand):
    help = "Создает тестовые данные: пользователи, роли, группы, расписание, связи"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Очистить основные таблицы перед созданием")

    def handle(self, *args, **options):
        if options.get("reset"):
            self.stdout.write("Очистка данных...")
            AthleteTrainingGroup.objects.all().delete()
            AthleteParent.objects.all().delete()
            GroupSchedule.objects.all().delete()
            TrainingGroup.objects.all().delete()
            Athlete.objects.all().delete()
            Parent.objects.all().delete()
            Trainer.objects.all().delete()
            Staff.objects.all().delete()
            # Пользователей не трогаем полностью, чтобы не потерять суперюзера

        self.stdout.write("Создание базовых групп Django...")
        managers_group, _ = Group.objects.get_or_create(name="Менеджеры")

        self.stdout.write("Создание персонала (Staff=manager)...")
        staff_users = []
        for i in range(1, 3 + 1):
            u, _ = User.objects.get_or_create(username=f"manager{i}", defaults={
                "first_name": f"Менеджер{i}",
                "last_name": "ЦСКА",
                "email": f"manager{i}@example.com",
            })
            u.set_password("pass1234"); u.is_active = True; u.save()
            staff, _ = Staff.objects.get_or_create(user=u, defaults={
                "phone": f"+790000000{i}",
                "birth_date": date(1990, 1, i),
                "role": "manager",
                "first_name": u.first_name,
                "last_name": u.last_name,
            })
            managers_group.user_set.add(u)
            staff_users.append(u)

        self.stdout.write("Создание тренеров...")
        trainers = []
        for i in range(1, 3 + 1):
            u, _ = User.objects.get_or_create(username=f"trainer{i}", defaults={
                "first_name": f"Тренер{i}",
                "last_name": "ЦСКА",
                "email": f"trainer{i}@example.com",
            })
            u.set_password("pass1234"); u.is_active = True; u.save()
            t, _ = Trainer.objects.get_or_create(user=u, defaults={
                "phone": f"+791000000{i}",
                "birth_date": date(1985, 2, i),
                "first_name": u.first_name,
                "last_name": u.last_name,
            })
            trainers.append(t)

        self.stdout.write("Создание тренировочных групп и расписаний...")
        groups = []
        group_specs = [
            ("Младшая группа", 6, 8, trainers[0]),
            ("Средняя группа", 9, 11, trainers[1]),
            ("Старшая группа", 12, 15, trainers[1]),
        ]
        for name, amin, amax, trainer in group_specs:
            g, _ = TrainingGroup.objects.get_or_create(
                name=name,
                defaults={
                    "age_min": amin,
                    "age_max": amax,
                    "trainer": trainer,
                    "max_athletes": 20,
                    "is_active": True,
                },
            )
            # Простое расписание: Пн/Ср 18:00-19:30
            GroupSchedule.objects.get_or_create(training_group=g, weekday=1, defaults={
                "start_time": time(18, 0), "end_time": time(19, 30)
            })
            GroupSchedule.objects.get_or_create(training_group=g, weekday=3, defaults={
                "start_time": time(18, 0), "end_time": time(19, 30)
            })
            groups.append(g)

        self.stdout.write("Создание родителей и детей с привязками...")
        parents = []
        for i in range(1, 5 + 1):
            u, _ = User.objects.get_or_create(username=f"parent{i}", defaults={
                "first_name": f"Родитель{i}",
                "last_name": "Иванов",
                "email": f"parent{i}@example.com",
            })
            u.set_password("pass1234"); u.is_active = True; u.save()
            p, _ = Parent.objects.get_or_create(user=u, defaults={
                "first_name": u.first_name,
                "last_name": u.last_name,
                "phone": f"+792000000{i}",
                "birth_date": date(1980, 5, i),
            })
            parents.append(p)

        athletes = []
        for i in range(1, 8 + 1):
            u, _ = User.objects.get_or_create(username=f"athlete{i}", defaults={
                "first_name": f"Спортсмен{i}",
                "last_name": "Петров",
                "email": f"athlete{i}@example.com",
            })
            u.set_password("pass1234"); u.is_active = True; u.save()
            a, _ = Athlete.objects.get_or_create(user=u, defaults={
                "first_name": u.first_name,
                "last_name": u.last_name,
                "birth_date": date(2012, (i % 12) + 1, (i % 27) + 1),
            })
            athletes.append(a)

        # Привязки ребенок-родитель (по 1-2 родителя на ребенка)
        for idx, a in enumerate(athletes):
            AthleteParent.objects.get_or_create(athlete=a, parent=parents[idx % len(parents)])
            if idx % 2 == 0 and len(parents) > 1:
                AthleteParent.objects.get_or_create(athlete=a, parent=parents[(idx + 1) % len(parents)])

        # Разбрасываем детей по группам равномерно
        for idx, a in enumerate(athletes):
            g = groups[idx % len(groups)]
            AthleteTrainingGroup.objects.get_or_create(athlete=a, training_group=g)

        self.stdout.write(self.style.SUCCESS("Тестовые данные созданы"))



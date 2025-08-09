"""
Management command для создания тестовых групп
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import TrainingGroup, GroupSchedule, Trainer


class Command(BaseCommand):
    help = 'Очищает все группы и создает новые тестовые группы без расписания'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-only',
            action='store_true',
            help='Только очистить группы, не создавать новые',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            # Сначала удаляем все расписания
            schedules_count = GroupSchedule.objects.count()
            GroupSchedule.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Удалено {schedules_count} записей расписания')
            )
            
            # Затем удаляем все группы
            groups_count = TrainingGroup.objects.count()
            TrainingGroup.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Удалено {groups_count} тренировочных групп')
            )
            
            if options['clear_only']:
                self.stdout.write(
                    self.style.SUCCESS('Очистка завершена. Новые группы не создавались.')
                )
                return
            
            # Создаем новые тестовые группы
            test_groups = [
                {
                    'name': 'Младшая группа (6-8 лет)',
                    'age_min': 6,
                    'age_max': 8,
                    'max_athletes': 15,
                    'is_active': True,
                },
                {
                    'name': 'Средняя группа (9-12 лет)', 
                    'age_min': 9,
                    'age_max': 12,
                    'max_athletes': 18,
                    'is_active': True,
                },
                {
                    'name': 'Старшая группа (13-16 лет)',
                    'age_min': 13,
                    'age_max': 16,
                    'max_athletes': 20,
                    'is_active': True,
                },
                {
                    'name': 'Взрослая группа (17+ лет)',
                    'age_min': 17,
                    'age_max': 99,
                    'max_athletes': 25,
                    'is_active': True,
                },
                {
                    'name': 'Подготовительная группа',
                    'age_min': 4,
                    'age_max': 6,
                    'max_athletes': 12,
                    'is_active': True,
                },
                {
                    'name': 'Профессиональная группа',
                    'age_min': 16,
                    'age_max': 30,
                    'max_athletes': 10,
                    'is_active': True,
                },
            ]
            
            # Получаем первого доступного тренера (если есть)
            trainer = Trainer.objects.filter(is_archived=False).first()
            if trainer:
                self.stdout.write(f'Найден тренер: {trainer}')
            else:
                self.stdout.write(
                    self.style.WARNING('Тренеры не найдены. Группы создаются без тренеров.')
                )
            
            created_groups = []
            for group_data in test_groups:
                # Добавляем тренера только к некоторым группам для разнообразия
                if trainer and len(created_groups) % 2 == 0:
                    group_data['trainer'] = trainer
                
                group = TrainingGroup.objects.create(**group_data)
                created_groups.append(group)
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Создана группа: {group.name}')
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Успешно создано {len(created_groups)} тестовых групп!'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  Расписание для групп НЕ создано. '
                    'Создайте расписание через админку Django.'
                )
            )

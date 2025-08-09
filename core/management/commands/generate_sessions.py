from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from core.models import TrainingGroup, GroupSchedule, TrainingSession

class Command(BaseCommand):
    help = "Генерирует тренировочные сессии на следующий месяц из расписания групп"

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=1,
            help='Количество месяцев вперед для генерации (по умолчанию 1)'
        )
        parser.add_argument(
            '--group',
            type=int,
            help='ID конкретной группы для генерации (если не указано - все группы)'
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        months_ahead = options['months']
        group_id = options.get('group')
        
        # Определяем период для генерации
        if months_ahead == 0:
            # Текущий месяц
            first_day = today.replace(day=1)
            if first_day.month == 12:
                next_first = first_day.replace(year=first_day.year+1, month=1, day=1)
            else:
                next_first = first_day.replace(month=first_day.month+1, day=1)
        else:
            # Следующие месяцы
            year = today.year
            month = today.month + months_ahead
            while month > 12:
                year += 1
                month -= 12
            
            first_day = date(year, month, 1)
            if month == 12:
                next_first = date(year+1, 1, 1)
            else:
                next_first = date(year, month+1, 1)

        self.stdout.write(f"Генерация сессий с {first_day} по {next_first - timedelta(days=1)}")

        # Фильтруем группы
        if group_id:
            groups = TrainingGroup.objects.filter(id=group_id, is_active=True, is_archived=False)
            if not groups:
                self.stdout.write(
                    self.style.ERROR(f'Группа с ID {group_id} не найдена или неактивна')
                )
                return
        else:
            groups = TrainingGroup.objects.filter(is_active=True, is_archived=False)

        created_count = 0
        skipped_count = 0

        for group in groups:
            self.stdout.write(f"Обрабатываем группу: {group}")
            
            # Получаем расписание группы
            schedules = GroupSchedule.objects.filter(training_group=group)
            if not schedules:
                self.stdout.write(f"  Нет расписания для группы {group}")
                continue

            # Генерируем сессии по каждому дню периода
            current_date = first_day
            while current_date < next_first:
                # Проверяем каждое расписание
                for schedule in schedules:
                    # weekday в модели: 1=Пн, 2=Вт, ..., 7=Вс
                    # weekday() в Python: 0=Пн, 1=Вт, ..., 6=Вс
                    if current_date.weekday() + 1 == schedule.weekday:
                        # Проверяем, существует ли уже сессия
                        existing_session = TrainingSession.objects.filter(
                            training_group=group,
                            date=current_date,
                            start_time=schedule.start_time
                        ).exists()
                        
                        if not existing_session:
                            # Создаем новую сессию
                            TrainingSession.objects.create(
                                training_group=group,
                                date=current_date,
                                start_time=schedule.start_time,
                                end_time=schedule.end_time,
                                is_closed=False,
                                is_canceled=False
                            )
                            created_count += 1
                            self.stdout.write(f"  ✓ Создана сессия на {current_date} в {schedule.start_time}")
                        else:
                            skipped_count += 1
                            self.stdout.write(f"  → Сессия на {current_date} в {schedule.start_time} уже существует")
                
                current_date += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(
                f'Генерация завершена! Создано сессий: {created_count}, пропущено: {skipped_count}'
            )
        )
from django.core.management.base import BaseCommand
from core.models import TrainingSession, TrainingGroup, GroupSchedule


class Command(BaseCommand):
    help = 'Проверка тренировочных сессий и их создания'

    def handle(self, *args, **options):
        self.stdout.write("=== Проверка тренировочных сессий ===")
        
        total_sessions = TrainingSession.objects.count()
        self.stdout.write(f"Всего сессий: {total_sessions}")

        # Проверим группы
        groups = TrainingGroup.objects.all()
        self.stdout.write(f"Всего групп: {groups.count()}")

        for group in groups:
            self.stdout.write(f"\nГруппа: {group.name}")
            schedules = GroupSchedule.objects.filter(training_group=group)
            self.stdout.write(f"  Расписаний: {schedules.count()}")
            
            sessions = TrainingSession.objects.filter(training_group=group)
            self.stdout.write(f"  Сессий: {sessions.count()}")
            
            if sessions.exists():
                self.stdout.write("  Даты сессий:")
                for session in sessions[:5]:  # Показываем первые 5
                    self.stdout.write(f"    {session.date} {session.start_time}-{session.end_time}")
                if sessions.count() > 5:
                    self.stdout.write(f"    ... и еще {sessions.count() - 5} сессий")

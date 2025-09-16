from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import TrainingGroup
from core.utils.enhanced_sessions import auto_ensure_yearly_schedule, ensure_yearly_sessions_for_group
from datetime import date

class Command(BaseCommand):
    help = "Test automatic yearly session generation for all groups"

    def add_arguments(self, parser):
        parser.add_argument(
            '--group-id',
            type=int,
            help='Test only specific group ID'
        )
        parser.add_argument(
            '--force-next-year',
            action='store_true',
            help='Force creation of sessions for next year'
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        group_id = options.get('group_id')
        force_next_year = options.get('force_next_year', False)
        
        self.stdout.write(f"🚀 Тестирование автоматического создания сессий на {today}")
        
        # Выбираем группы
        if group_id:
            groups = TrainingGroup.objects.filter(id=group_id, is_active=True, is_archived=False)
            if not groups.exists():
                self.stdout.write(self.style.ERROR(f'Группа с ID {group_id} не найдена'))
                return
        else:
            groups = TrainingGroup.objects.filter(is_active=True, is_archived=False)
        
        total_created = 0
        
        for group in groups:
            self.stdout.write(f"\n📋 Обрабатываем группу: {group.name}")
            
            # Показываем текущие сессии
            current_sessions = group.trainingsession_set.filter(date__year=today.year).count()
            next_year_sessions = group.trainingsession_set.filter(date__year=today.year + 1).count()
            
            self.stdout.write(f"  📊 Текущий год ({today.year}): {current_sessions} сессий")
            self.stdout.write(f"  📊 Следующий год ({today.year + 1}): {next_year_sessions} сессий")
            
            # Тестируем автоматическое создание
            created = auto_ensure_yearly_schedule(group)
            total_created += created
            
            if created > 0:
                self.stdout.write(self.style.SUCCESS(f"  ✅ Создано {created} новых сессий"))
            else:
                self.stdout.write("  ℹ️ Новые сессии не требуются")
            
            # Если нужно принудительно создать сессии на следующий год
            if force_next_year:
                next_year_start = date(today.year + 1, 1, 1)
                next_year_created = ensure_yearly_sessions_for_group(group, next_year_start)
                if next_year_created > 0:
                    self.stdout.write(self.style.SUCCESS(f"  🔮 Принудительно создано {next_year_created} сессий на {today.year + 1} год"))
                    total_created += next_year_created
        
        self.stdout.write(f"\n🎯 Итого создано сессий: {total_created}")
        
        if total_created > 0:
            self.stdout.write(self.style.SUCCESS("✨ Автоматическое создание сессий работает!"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Новые сессии не были созданы (возможно, уже существуют)"))
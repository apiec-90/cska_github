from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Создает базовые группы без допусков и специализированные группы с допусками'

    def handle(self, *args, **options):
        self.stdout.write('Настройка иерархической системы групп...')
        
        # Создаем базовые группы (без допусков)
        base_groups = ['Спортсмены', 'Родители', 'Тренеры', 'Сотрудники']
        
        for group_name in base_groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'✓ Создана группа: {group_name}')
            else:
                self.stdout.write(f'✓ Группа уже существует: {group_name}')
            
            # Очищаем разрешения из базовых групп
            if group.permissions.exists():
                group.permissions.clear()
                self.stdout.write(f'  → Очищены разрешения из группы: {group_name}')
        
        # Создаем специализированные группы для staff
        staff_groups = ['Менеджеры', 'Администраторы']
        
        for group_name in staff_groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'✓ Создана группа: {group_name}')
            else:
                self.stdout.write(f'✓ Группа уже существует: {group_name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Иерархическая система групп настроена!\n'
                '📋 Структура:\n'
                '  • Базовые группы (без допусков): Спортсмены, Родители, Тренеры, Сотрудники\n'
                '  • Специализированные группы (с допусками): Менеджеры, Администраторы\n'
                '  • Пользователи получают базовую группу + специализированную (для staff)\n\n'
                '💡 Теперь вы можете:\n'
                '  1. Добавлять новые группы в админке\n'
                '  2. Назначать допуски только в специализированных группах\n'
                '  3. Обновлять маппинг в core/utils.py для новых групп'
            )
        )





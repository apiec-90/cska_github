from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Добавляет новую группу для сотрудников'

    def add_arguments(self, parser):
        parser.add_argument('group_name', type=str, help='Название новой группы')
        parser.add_argument('--subrole', type=str, help='Код подроли (например, accountant)')

    def handle(self, *args, **options):
        group_name = options['group_name']
        subrole = options.get('subrole')
        
        if not subrole:
            subrole = group_name.lower().replace(' ', '_').replace('-', '_')
        
        # Создаем группу
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            self.stdout.write(f'✓ Создана группа: {group_name}')
        else:
            self.stdout.write(f'✓ Группа уже существует: {group_name}')
        
        # Показываем инструкции для обновления кода
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Группа "{group_name}" готова к использованию!\n\n'
                f'📝 Для полной интеграции добавьте в core/utils.py:\n'
                f'   subrole_to_group = {{\n'
                f'       "manager": "Менеджеры",\n'
                f'       "admin": "Администраторы",\n'
                f'       "{subrole}": "{group_name}",  # ← добавьте эту строку\n'
                f'   }}\n\n'
                f'💡 Теперь вы можете:\n'
                f'  1. Назначить допуски группе "{group_name}" в админке\n'
                f'  2. Обновить Staff.ROLE_CHOICES в models.py если нужно\n'
                f'  3. Использовать подроль "{subrole}" при регистрации'
            )
        )

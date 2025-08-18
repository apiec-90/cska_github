from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Показывает все группы и их разрешения'

    def handle(self, *args, **options):
        self.stdout.write('📋 Список всех групп:\n')
        
        groups = Group.objects.all().order_by('name')
        
        for group in groups:
            self.stdout.write(f'\n🔹 {group.name}')
            
            if group.permissions.exists():
                self.stdout.write('  Разрешения:')
                for perm in group.permissions.all():
                    self.stdout.write(f'    • {perm.codename} ({perm.content_type.app_label}.{perm.content_type.model})')
            else:
                self.stdout.write('  Разрешений нет (базовая группа)')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Всего групп: {groups.count()}\n'
                '💡 Базовые группы (без разрешений) используются для классификации\n'
                '💡 Специализированные группы (с разрешениями) используются для доступа'
            )
        )






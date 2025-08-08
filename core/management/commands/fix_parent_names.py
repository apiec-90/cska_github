from django.core.management.base import BaseCommand
from core.models import Parent


class Command(BaseCommand):
    help = 'Исправляет ФИО в существующих записях Parent из User'

    def handle(self, *args, **options):
        parents = Parent.objects.select_related('user').all()
        fixed_count = 0
        
        for parent in parents:
            updated = False
            
            # Если у Parent нет first_name, но у User есть
            if not parent.first_name and parent.user.first_name:
                parent.first_name = parent.user.first_name
                updated = True
                self.stdout.write(f"  Parent {parent.id}: установлен first_name = '{parent.user.first_name}'")
            
            # Если у Parent нет last_name, но у User есть
            if not parent.last_name and parent.user.last_name:
                parent.last_name = parent.user.last_name
                updated = True
                self.stdout.write(f"  Parent {parent.id}: установлен last_name = '{parent.user.last_name}'")
            
            if updated:
                parent.save(update_fields=['first_name', 'last_name'])
                fixed_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Исправлено {fixed_count} записей Parent из {parents.count()} всего')
        )

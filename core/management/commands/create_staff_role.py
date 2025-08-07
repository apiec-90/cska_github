from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from core.models import CustomStaffRole, Staff, Parent, Athlete, TrainingGroup, Document, Payment

class Command(BaseCommand):
    help = 'Создает новую кастомную роль для сотрудников с допусками'

    def add_arguments(self, parser):
        parser.add_argument('role_name', type=str, help='Название роли (например: cleaner)')
        parser.add_argument('display_name', type=str, help='Отображаемое название (например: Уборщица)')
        parser.add_argument('permissions', nargs='+', help='Список прав (view_athlete, add_payment)')

    def handle(self, *args, **options):
        role_name = options['role_name']
        display_name = options['display_name']
        permissions = options['permissions']
        
        # Проверяем, не существует ли уже такая роль
        existing_role = CustomStaffRole.objects.filter(name=role_name).first()
        if existing_role:
            self.stdout.write(
                self.style.WARNING(f'Роль "{display_name}" уже существует!')
            )
            return
        
        # Создаем новую роль
        role = CustomStaffRole.objects.create(
            name=role_name,
            display_name=display_name,
            description=f"Создана через команду: {display_name}"
        )
        
        self.stdout.write(f'Создана роль: {display_name}')
        
        # Добавляем права
        perms = []
        for perm_name in permissions:
            try:
                # Парсим permission (action_model)
                if '_' in perm_name:
                    action, model_name = perm_name.split('_', 1)
                    
                    # Определяем модель
                    model_mapping = {
                        'athlete': Athlete,
                        'parent': Parent,
                        'staff': Staff,
                        'traininggroup': TrainingGroup,
                        'trainingsession': 'TrainingSession',
                        'attendancerecord': 'AttendanceRecord',
                        'payment': Payment,
                        'document': Document,
                    }
                    
                    if model_name in model_mapping:
                        model = model_mapping[model_name]
                        if isinstance(model, str):
                            # Для связанных моделей
                            content_type = ContentType.objects.get(app_label='core', model=model.lower())
                        else:
                            content_type = ContentType.objects.get_for_model(model)
                        
                        permission = Permission.objects.get(
                            content_type=content_type,
                            codename=f'{action}_{model_name}'
                        )
                        perms.append(permission)
                        
            except (Permission.DoesNotExist, ContentType.DoesNotExist):
                self.stdout.write(
                    self.style.WARNING(f'Право не найдено: {perm_name}')
                )
        
        # Добавляем права к роли
        role.permissions.set(perms)
        self.stdout.write(f'Добавлено {len(perms)} прав к роли {display_name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Роль "{display_name}" создана успешно! Теперь можно назначать сотрудникам роль "{role_name}"')
        )

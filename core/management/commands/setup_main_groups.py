from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Staff, Parent, Athlete, Trainer, TrainingGroup, Document, Payment

class Command(BaseCommand):
    help = 'Создает основные группы: Родители, Спортсмены, Тренеры, Сотрудники'

    def handle(self, *args, **options):
        self.stdout.write('Создаем основные группы...')
        
        # Определяем группы и их права
        groups_config = {
            'Родители': {
                'description': 'Родители спортсменов',
                'permissions': [
                    'view_athlete',
                    'view_traininggroup', 
                    'view_trainingsession',
                    'view_attendancerecord',
                    'view_payment',
                ]
            },
            'Спортсмены': {
                'description': 'Спортсмены',
                'permissions': [
                    'view_traininggroup',
                    'view_trainingsession',
                    'view_attendancerecord',
                ]
            },
            'Тренеры': {
                'description': 'Тренеры спортивных групп',
                'permissions': [
                    'view_athlete', 'add_athlete', 'change_athlete',
                    'view_traininggroup', 'add_traininggroup', 'change_traininggroup',
                    'view_trainingsession', 'add_trainingsession', 'change_trainingsession',
                    'view_attendancerecord', 'add_attendancerecord', 'change_attendancerecord',
                    'view_document', 'add_document', 'change_document',
                ]
            },
            'Сотрудники': {
                'description': 'Вспомогательные сотрудники',
                'permissions': [
                    'view_athlete', 'view_parent',
                    'view_traininggroup', 'view_trainingsession',
                    'view_attendancerecord', 'view_payment',
                    'view_document',
                ]
            }
        }
        
        for group_name, config in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(f'Создана группа: {group_name}')
            else:
                self.stdout.write(f'Группа уже существует: {group_name}')
            
            # Добавляем права
            permissions = []
            for perm_name in config['permissions']:
                try:
                    # Парсим permission (action_model)
                    if '_' in perm_name:
                        action, model_name = perm_name.split('_', 1)
                        
                        # Определяем модель
                        model_mapping = {
                            'athlete': Athlete,
                            'parent': Parent,
                            'staff': Staff,
                            'trainer': Trainer,
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
                            permissions.append(permission)
                            
                except (Permission.DoesNotExist, ContentType.DoesNotExist):
                    self.stdout.write(
                        self.style.WARNING(f'Право не найдено: {perm_name}')
                    )
            
            # Добавляем права к группе
            group.permissions.set(permissions)
            self.stdout.write(f'Добавлено {len(permissions)} прав к группе {group_name}')
        
        self.stdout.write(
            self.style.SUCCESS('Основные группы созданы успешно!')
        )
        self.stdout.write(
            self.style.SUCCESS('Теперь можно создавать кастомные роли через: python manage.py create_staff_role')
        )

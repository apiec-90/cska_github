from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from core.models import Staff, Parent, Athlete
from core.signals import GROUP_MODEL_MAPPING

class Command(BaseCommand):
    help = 'Синхронизирует пользователей с их ролями на основе групп'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем синхронизацию пользователей с ролями...')
        
        # Отключаем сигналы на время синхронизации
        from django.db.models.signals import m2m_changed
        from core.signals import create_role_records, remove_role_records
        m2m_changed.disconnect(create_role_records, sender=User.groups.through)
        m2m_changed.disconnect(remove_role_records, sender=User.groups.through)
        
        try:
            for user in User.objects.all():
                user_groups = user.groups.all()
                
                for group in user_groups:
                    if group.name in GROUP_MODEL_MAPPING:
                        config = GROUP_MODEL_MAPPING[group.name]
                        model_class = config['model']
                        role = config.get('role')
                        
                        # Проверяем, есть ли уже запись
                        existing_record = model_class.objects.filter(user=user).first()
                        
                        if not existing_record:
                            # Создаем новую запись
                            if role:
                                # Для Staff с ролью и дефолтными значениями
                                from datetime import date
                                new_record = model_class.objects.create(
                                    user=user, 
                                    role=role,
                                    birth_date=date(1990, 1, 1),  # Дефолтная дата
                                    phone=f"+7{user.id:09d}",  # Дефолтный телефон
                                )
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Создана запись {model_class.__name__} для {user.username} в группе {group.name} с ролью {role}'
                                    )
                                )
                            else:
                                # Для Parent и Athlete без ролей
                                new_record = model_class.objects.create(user=user)
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Создана запись {model_class.__name__} для {user.username} в группе {group.name}'
                                    )
                                )
                        else:
                            # Если запись уже существует, обновляем роль (только для Staff)
                            if isinstance(existing_record, Staff) and role:
                                if existing_record.role != role:
                                    old_role = existing_record.role
                                    existing_record.role = role
                                    existing_record.save(update_fields=['role'])
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f'Обновлена роль для {user.username}: {old_role} → {role}'
                                        )
                                    )
                                else:
                                    self.stdout.write(
                                        f'Запись {model_class.__name__} для {user.username} уже существует с ролью {role}'
                                    )
                            else:
                                self.stdout.write(
                                    f'Запись {model_class.__name__} для {user.username} уже существует'
                                )
            
            self.stdout.write(
                self.style.SUCCESS('Синхронизация завершена успешно!')
            )
            
        finally:
            # Включаем сигналы обратно
            m2m_changed.connect(create_role_records, sender=User.groups.through)
            m2m_changed.connect(remove_role_records, sender=User.groups.through)

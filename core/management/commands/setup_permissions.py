from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Настраивает разрешения для специализированных групп'

    def handle(self, *args, **options):
        self.stdout.write('Настройка разрешений для специализированных групп...')
        
        # Получаем все content types
        content_types = ContentType.objects.all()
        permission_map = {}
        
        for ct in content_types:
            model_name = ct.model
            app_label = ct.app_label
            
            # Создаем маппинг разрешений
            for action in ['add', 'change', 'delete', 'view']:
                codename = f'{action}_{model_name}'
                try:
                    perm = Permission.objects.get(
                        content_type=ct,
                        codename=codename
                    )
                    permission_map[codename] = perm
                except Permission.DoesNotExist:
                    pass
        
        # Настройка разрешений для Менеджеров
        manager_permissions = [
            'add_staff', 'change_staff', 'delete_staff', 'view_staff',
            'add_athlete', 'change_athlete', 'delete_athlete', 'view_athlete',
            'add_trainer', 'change_trainer', 'delete_trainer', 'view_trainer',
            'add_parent', 'change_parent', 'delete_parent', 'view_parent',
            'add_document', 'change_document', 'delete_document', 'view_document',
            'add_traininggroup', 'change_traininggroup', 'delete_traininggroup', 'view_traininggroup',
        ]
        
        try:
            managers_group = Group.objects.get(name='Менеджеры')
            permissions_to_add = []
            for perm_codename in manager_permissions:
                if perm_codename in permission_map:
                    permissions_to_add.append(permission_map[perm_codename])
            
            managers_group.permissions.set(permissions_to_add)
            self.stdout.write(f'✓ Назначено {len(permissions_to_add)} разрешений группе "Менеджеры"')
        except Group.DoesNotExist:
            self.stdout.write('⚠ Группа "Менеджеры" не найдена')
        
        # Настройка разрешений для Администраторов (все разрешения)
        try:
            admins_group = Group.objects.get(name='Администраторы')
            all_permissions = list(permission_map.values())
            admins_group.permissions.set(all_permissions)
            self.stdout.write(f'✓ Назначено {len(all_permissions)} разрешений группе "Администраторы"')
        except Group.DoesNotExist:
            self.stdout.write('⚠ Группа "Администраторы" не найдена')
        
        # Настройка разрешений для Бухгалтеров (ограниченные)
        accountant_permissions = [
            'view_staff', 'view_athlete', 'view_trainer', 'view_parent',
            'view_document', 'view_traininggroup',
            'add_document', 'change_document',
        ]
        
        try:
            accountants_group = Group.objects.get(name='Бухгалтеры')
            permissions_to_add = []
            for perm_codename in accountant_permissions:
                if perm_codename in permission_map:
                    permissions_to_add.append(permission_map[perm_codename])
            
            accountants_group.permissions.set(permissions_to_add)
            self.stdout.write(f'✓ Назначено {len(permissions_to_add)} разрешений группе "Бухгалтеры"')
        except Group.DoesNotExist:
            self.stdout.write('⚠ Группа "Бухгалтеры" не найдена')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Разрешения настроены!\n'
                '📋 Структура доступа:\n'
                '  • Менеджеры: полный доступ к управлению данными\n'
                '  • Администраторы: полный доступ ко всему\n'
                '  • Бухгалтеры: просмотр + работа с документами\n'
                '  • Базовые группы: без разрешений (только классификация)'
            )
        )












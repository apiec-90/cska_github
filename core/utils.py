from django.contrib.auth.models import Group, User
from typing import Optional


def assign_groups_for_registration(user: User, role: str, subrole: Optional[str] = None) -> None:
    """
    Назначает Django-группы пользователю по роли и подроли.
    
    Args:
        user: Пользователь для назначения групп
        role: Основная роль (trainer, athlete, parent, staff)
        subrole: Подроль для staff (например, 'manager')
    """
    # Очищаем существующие группы пользователя
    user.groups.clear()
    
    # Маппинг ролей на базовые группы
    role_to_group = {
        'trainer': 'Тренеры',
        'athlete': 'Спортсмены', 
        'parent': 'Родители',
        'staff': 'Сотрудники',
    }
    
    # Назначаем базовую группу по роли
    if role in role_to_group:
        group_name = role_to_group[role]
        group, created = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    
    # Для staff добавляем группу подроли
    if role == 'staff' and subrole:
        subrole_to_group = {
            'manager': 'Менеджеры',
            'admin': 'Администраторы',
            'accountant': 'Бухгалтеры',
            # Добавляйте новые группы здесь:
            # 'hr': 'HR-специалисты',
            # 'security': 'Охрана',
        }
        if subrole in subrole_to_group:
            subrole_group_name = subrole_to_group[subrole]
            subrole_group, created = Group.objects.get_or_create(name=subrole_group_name)
            user.groups.add(subrole_group)

# Импорт админок из модулей для лучшей организации кода
# Прямой импорт из модулей для избежания циклических импортов
from .admin.base import *
from .admin.user_admins import *
from .admin.group_admins import *
from .admin.other_admins import *

# Модульная архитектура админок:
# - Trainer, Parent, Athlete, Staff: core.admin.user_admins
# - TrainingGroup и другие: core.admin.group_admins
# - Остальные модели: core.admin.other_admins
# 
# Дублирующие регистрации удалены для предотвращения конфликтов URL
# Все основные админские классы теперь находятся в соответствующих модулях

# This file now serves as the main entry point that imports all admin modules
# while avoiding duplicate registrations that were causing URL resolution errors


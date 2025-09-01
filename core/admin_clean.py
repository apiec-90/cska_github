# Импорт админок из модулей для лучшей организации кода
from .admin import *

# Остальной код admin.py временно перемещен в модули
# Здесь остаются только ссылки на модульную архитектуру

# Note: Админки для TrainerAdmin, ParentAdmin, AthleteAdmin теперь обрабатываются в core.admin.user_admins
# чтобы избежать дублирования регистраций и ошибок URL

# URL'ы для регистрации теперь находятся в core.admin.base.CustomUserAdmin
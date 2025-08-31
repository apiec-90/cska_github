# Admin package for CSKA Django CRM
# Разделение admin.py на модули для улучшения архитектуры

# Импортируем модули в правильном порядке
from . import base
from . import user_admins
from . import group_admins 
from . import other_admins

# Экспортируем все классы
from .base import *
from .user_admins import *
from .group_admins import *
from .other_admins import *
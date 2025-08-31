# 🔧 Спецификация для разработчика - ЦСКА Django CRM

## 📊 Анализ проекта

### Архитектура и структура
Проект представляет Django-приложение для управления спортивным клубом с функциями регистрации, управления группами, расписанием и посещаемостью.

### Качество кода
**Оценка: 7/10**
- ✅ Хорошая структура моделей
- ⚠️ Дублирование кода в admin.py
- ✅ Использование сигналов
- ⚠️ Избыточные комментарии
- ✅ Правильная архитектура MTV

## 🏗️ Архитектура системы

### Основные компоненты
```
cska_django_supabase/
├── core/                    # Основное приложение
│   ├── models.py           # Модели данных
│   ├── admin.py            # Интерфейс администратора 
│   ├── views.py            # Представления
│   ├── forms.py            # Формы
│   ├── utils/              # Утилиты
│   ├── management/         # Команды управления
│   └── templates/          # Шаблоны
├── static/                 # Статические файлы
├── templates/              # Общие шаблоны
└── media/                  # Загруженные файлы
```

### Модели данных

#### Пользователи системы
```python
# Базовые роли наследуют от User
User (Django)
├── Trainer    # Тренеры - ведут группы
├── Staff      # Сотрудники - управляют системой
├── Parent     # Родители - связаны с детьми
└── Athlete    # Спортсмены - участвуют в тренировках
```

#### Структура тренировок
```python
TrainingGroup           # Тренировочная группа
├── GroupSchedule      # Расписание группы (дни/время)
├── TrainingSession    # Конкретная тренировка
└── AttendanceRecord   # Посещаемость спортсменов
```

#### Связи
```python
AthleteTrainingGroup   # М2М: Спортсмен ↔ Группа
AthleteParent         # М2М: Спортсмен ↔ Родитель
```

#### Дополнительные
```python
Payment               # Платежи
Document             # Документы (файлы)
AuditRecord          # Аудит действий
RegistrationDraft    # Черновики регистрации
```

## 💾 База данных

### PostgreSQL (рекомендуемая)
```sql
-- Основные таблицы
trainer               # Тренеры
staff                # Сотрудники  
parent               # Родители
athlete              # Спортсмены
training_group       # Группы
group_schedule       # Расписание
training_session     # Сессии
attendance_record    # Посещаемость
```

### Миграции
**Проблема:** 23 миграции указывают на нестабильную модель данных
```bash
# Последние критичные миграции
0020_alter_attendancerecord_athlete_trainingsession.py
0021_auto_20250821_1503.py  
0022_auto_20250821_1527.py
0023_auto_20250821_1541.py
```

## 🔍 Проблемы качества кода

### 1. Дублирование в admin.py (КРИТИЧНО)
**Проблема:** Дублируются методы между Admin классами
```python
# Повторяется в TrainerAdmin, StaffAdmin, ParentAdmin
def get_full_name(self, obj):
def get_phone(self, obj): 
def get_active_status(self, obj):
def get_queryset(self, request):
```

**Решение:** Создать базовый класс
```python
class BasePersonAdmin(admin.ModelAdmin):
    def get_full_name(self, obj):
        # Общая логика
        
class TrainerAdmin(BasePersonAdmin):
    # Специфичная логика тренера
```

### 2. Размер файлов
- `admin.py`: 2696 строк (СЛИШКОМ БОЛЬШОЙ)
- `models.py`: 432 строки (НОРМА)
- `forms.py`: 355 строк (НОРМА)

**Решение:** Разделить admin.py на модули
```python
core/admin/
├── __init__.py
├── base.py      # Базовые классы
├── trainer.py   # TrainerAdmin
├── athlete.py   # AthleteAdmin
└── staff.py     # StaffAdmin
```

### 3. Избыточные комментарии
```python
# Плохо: очевидные комментарии
phone = models.CharField(max_length=255, verbose_name="Телефон")  # Телефон

# Хорошо: комментарии с бизнес-логикой  
phone = models.CharField(max_length=255, verbose_name="Телефон")  # Обязательно для SMS-уведомлений
```

### 4. Повторяющаяся логика
**Проблема:** Дублирование логики создания сессий
- В `forms.py` - метод `_generate_training_sessions`
- В `utils/sessions.py` - функции создания сессий

**Решение:** Централизовать в utils

## 🛠️ Техническая архитектура

### Стек технологий
```yaml
Backend: Django 5.2.4+
Database: PostgreSQL (через psycopg2-binary 2.9.9)
Images: Pillow 10.0.0
Frontend: Django Admin + Jazzmin
Cache: Нет (рекомендуется Redis)
Queue: Нет (рекомендуется Celery)
```

### Производительность
**Текущие проблемы:**
- Отсутствует кеширование
- N+1 запросы в admin списках
- Нет пагинации для больших таблиц

**Решения:**
```python
# Оптимизация запросов
def get_queryset(self, request):
    return super().get_queryset(request).select_related(
        'user', 'trainer'
    ).prefetch_related('athletetraininggroup_set')

# Кеширование
from django.core.cache import cache

@cache_page(300)  # 5 минут
def expensive_view(request):
    pass
```

## 🔐 Безопасность

### Текущие меры
✅ CSRF защита включена
✅ Аутентификация через Django Admin
✅ Валидация форм
✅ Права доступа через Groups

### Проблемы безопасности
⚠️ DEBUG=True в продакшене
⚠️ SECRET_KEY в коде
⚠️ Отсутствует HTTPS принуждение
⚠️ Нет rate limiting

### Рекомендации
```python
# settings.py для продакшена
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
```

## 📋 Система прав доступа

### Группы пользователей
```python
# Базовые группы (без прав)
"Спортсмены"    # Для Athlete
"Родители"      # Для Parent  
"Тренеры"       # Для Trainer
"Сотрудники"    # Для Staff (базовая)

# Специализированные группы (с правами)
"Менеджеры"         # 24 разрешения
"Администраторы"    # 92 разрешения  
"Бухгалтеры"        # Настраивается
```

### Логика назначения
```python
# При регистрации Staff
if staff.role == 'manager':
    user.groups.add("Сотрудники", "Менеджеры")
elif staff.role == 'admin': 
    user.groups.add("Сотрудники", "Администраторы")
```

## 🔄 Автоматизация и сигналы

### Система сигналов
```python
# Автоматическое создание сессий при изменении расписания
@receiver([post_save, post_delete], sender=GroupSchedule)
def on_schedule_change(sender, instance, **kwargs):
    resync_future_sessions_for_group(instance.training_group)
```

### Команды управления
```bash
# Создание структуры групп
python manage.py setup_groups
python manage.py setup_permissions

# Управление сессиями  
python manage.py generate_sessions
python manage.py generate_sessions --all-groups-next-month

# Тестирование
python manage.py create_test_data
```

## 🧪 Тестирование

### Текущее состояние
⚠️ Тесты отсутствуют в проекте
📁 Есть файл `test_signals.py` для ручного тестирования

### Рекомендуемая структура
```python
core/tests/
├── __init__.py
├── test_models.py      # Тесты моделей
├── test_views.py       # Тесты представлений
├── test_admin.py       # Тесты админки
├── test_forms.py       # Тесты форм
└── test_signals.py     # Тесты сигналов
```

## 📊 Мониторинг и логирование

### Аудит действий
```python
# Модель AuditRecord логирует:
- Действия пользователей
- Изменения данных
- Временные метки
- Детали операций
```

### Рекомендуемое логирование
```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'app.log',
        },
    },
    'loggers': {
        'core': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

## 🚀 Рекомендации по улучшению

### Критичные (приоритет 1)
1. **Разделить admin.py на модули** - размер 2696 строк критичен
2. **Устранить дублирование кода** - создать базовые классы
3. **Добавить тесты** - покрытие 0% недопустимо
4. **Настроить продакшен** - DEBUG=False, переменные окружения

### Важные (приоритет 2)  
1. **Добавить кеширование** - Redis для сессий и запросов
2. **Оптимизировать запросы** - устранить N+1
3. **Добавить API** - Django REST Framework
4. **Настроить мониторинг** - Sentry для ошибок

### Желательные (приоритет 3)
1. **Добавить очереди** - Celery для тяжелых операций
2. **Улучшить UI** - современный фронтенд
3. **Добавить мобильное приложение**
4. **Интеграция с внешними системами**

## 📈 Масштабирование

### Узкие места
- Одна база данных
- Отсутствие кеширования
- Синхронная обработка

### Решения
```python
# Разделение чтения/записи
DATABASE_ROUTERS = ['core.routers.DatabaseRouter']

# Кеширование запросов
from django.core.cache import cache

# Асинхронные задачи
from celery import shared_task
```

## 🔧 Команды разработчика

### Запуск проекта
```bash
# Установка зависимостей
pip install -r requirements.txt

# Миграции
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Запуск сервера
python manage.py runserver
```

### Разработка
```bash
# Создание миграций
python manage.py makemigrations

# Сбор статики
python manage.py collectstatic

# Команды проекта
python manage.py setup_groups
python manage.py generate_sessions
```

## 📝 Соглашения разработки

### Код
- Python: PEP 8
- Django: следовать best practices
- Комментарии: на русском для бизнес-логики
- Имена: английские для кода, русские для verbose_name

### Git
```bash
# Ветки
feature/название-функции
bugfix/описание-бага
hotfix/критичная-правка

# Коммиты на русском
git commit -m "Добавить валидацию телефона в форму спортсмена"
```

### Документация
- Обновлять при изменении API
- Комментировать сложную бизнес-логику
- Вести changelog изменений

## 🎯 Заключение

Проект имеет хорошую архитектурную основу, но требует рефакторинга для улучшения качества кода и производительности. Основные проблемы решаются стандартными Django-практиками.

**Время на рефакторинг:** 2-3 недели  
**Приоритет:** Критичные проблемы решить в первую очередь
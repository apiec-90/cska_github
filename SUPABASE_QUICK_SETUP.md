# Быстрая настройка Supabase для Django проекта

## 1. Создайте файл .env в корне проекта

Скопируйте содержимое из `env_template.txt` в новый файл `.env`:

```bash
# В PowerShell/CMD
copy env_template.txt .env
```

## 2. Получите данные из Supabase Dashboard

1. Зайдите на [supabase.com](https://supabase.com) и войдите в аккаунт
2. Создайте новый проект или откройте существующий
3. Перейдите в **Settings** → **API**
4. Скопируйте следующие значения:

### Обязательные настройки:
- **Project URL** → замените `SUPABASE_URL` в .env
- **anon public** ключ → замените `SUPABASE_ANON_KEY` в .env  
- **service_role** ключ → замените `SUPABASE_SERVICE_KEY` в .env

### Для подключения к базе данных:
1. Перейдите в **Settings** → **Database**
2. Найдите **Connection string** → **URI**
3. Скопируйте строку подключения и замените `DATABASE_URL` в .env

Пример:
```env
DATABASE_URL=postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres
```

## 3. Проверьте подключение

```bash
# Проверьте, что Django видит переменные окружения
python manage.py shell -c "import os; print('SUPABASE_URL:', os.environ.get('SUPABASE_URL'))"

# Проверьте подключение к базе данных
python manage.py check --database default
```

## 4. Примените миграции

```bash
# Создайте миграции (если нужно)
python manage.py makemigrations

# Примените миграции к Supabase
python manage.py migrate
```

## 5. Создайте суперпользователя

```bash
python manage.py createsuperuser
```

## Возможные проблемы:

### Ошибка "Import dj_database_url could not be resolved"
- Убедитесь, что `dj-database-url` установлен: `pip install dj-database-url==2.2.0`
- Перезапустите IDE/редактор кода

### Ошибка подключения к базе данных
- Проверьте правильность `DATABASE_URL` в .env
- Убедитесь, что пароль не содержит специальных символов (или экранируйте их)
- Проверьте, что проект Supabase активен и не приостановлен

### Ошибки миграций
- Убедитесь, что база данных пуста или совместима с текущими миграциями
- При необходимости сбросьте миграции: `python manage.py migrate --fake-initial`

## Структура проекта после настройки:

```
cska_django_supabase/
├── .env                    # Переменные окружения (не в Git!)
├── env_template.txt        # Шаблон для .env
├── requirements.txt        # Зависимости Python
├── manage.py              # Django управление
└── cska_django_supabase/
    └── settings.py        # Настройки Django
```

## Полезные команды:

```bash
# Проверка статуса проекта
python manage.py check

# Просмотр SQL миграций
python manage.py sqlmigrate core 0001

# Откат миграций
python manage.py migrate core 0001

# Сброс базы данных (осторожно!)
python manage.py flush
```

# Настройка переменных окружения

## Создайте файл .env в корне проекта:

```env
# Supabase настройки
SUPABASE_URL=https://gzrefdsqgynnvdodubiu.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Storage настройки
SUPABASE_STORAGE_BUCKET=media
UPLOAD_FOLDER=media

# Django настройки
DEBUG=True
SECRET_KEY=your-secret-key-here
```

## Важные моменты:

1. **SUPABASE_STORAGE_BUCKET** - точное название bucket в Supabase (регистр имеет значение)
2. **UPLOAD_FOLDER** - локальная папка с файлами для загрузки
3. **SUPABASE_SERVICE_ROLE_KEY** - нужен для создания bucket и загрузки файлов

## Получение ключей:

1. Зайдите в [Supabase Dashboard](https://supabase.com/dashboard)
2. Выберите ваш проект
3. Перейдите в **Settings** → **API**
4. Скопируйте:
   - **anon** key → `SUPABASE_KEY`
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY`

## Создание bucket:

1. В Supabase Dashboard перейдите в **Storage**
2. Нажмите **Create a new bucket**
3. Назовите bucket точно как указано в `SUPABASE_STORAGE_BUCKET`
4. Установите **Public bucket** (если нужен публичный доступ) 
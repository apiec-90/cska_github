# Настройка Supabase для загрузки файлов

## Проблема
Текущий код использует `anon` key, который не имеет прав на:
- Создание bucket
- Загрузку файлов
- Управление storage

## Решение

### 1. Получите Service Role Key
1. Зайдите в [Supabase Dashboard](https://supabase.com/dashboard)
2. Выберите ваш проект
3. Перейдите в **Settings** → **API**
4. Скопируйте **service_role** key (НЕ anon key)

### 2. Создайте bucket вручную
1. В Supabase Dashboard перейдите в **Storage**
2. Нажмите **Create a new bucket**
3. Назовите bucket `media`
4. Установите **Public bucket** (если нужен публичный доступ)

### 3. Настройте RLS (Row Level Security)
Для bucket `media` создайте политику:

```sql
-- Разрешить всем пользователям читать файлы
CREATE POLICY "Public Access" ON storage.objects FOR SELECT USING (bucket_id = 'media');

-- Разрешить аутентифицированным пользователям загружать файлы
CREATE POLICY "Authenticated users can upload" ON storage.objects FOR INSERT 
WITH CHECK (bucket_id = 'media' AND auth.role() = 'authenticated');
```

### 4. Обновите переменные окружения
Создайте файл `.env` с правильными ключами:

```env
SUPABASE_URL=https://gzrefdsqgynnvdodubiu.supabase.co
SUPABASE_KEY=your-service-role-key-here
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_STORAGE_BUCKET=media
```

### 5. Обновите код
Используйте service_role key для операций с файлами:

```python
# Для загрузки файлов используйте service_role key
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "your-service-role-key")
```

## Альтернативное решение
Если нужно использовать только anon key, создайте bucket вручную и настройте RLS политики для публичного доступа. 
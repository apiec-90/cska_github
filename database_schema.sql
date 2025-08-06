-- Схема базы данных для спортивной школы CSKA
-- Создана на основе Django моделей
-- 
-- ОСОБЕННОСТИ АРХИТЕКТУРЫ:
-- 1. Роли автоматически синхронизируются с Django группами
-- 2. Разрешения ролей автоматически добавляются в Django группы
-- 3. При создании/изменении/удалении роли соответствующая Django группа обновляется автоматически
-- 4. Пользователи могут быть добавлены в Django группы для проверки разрешений

-- Создание таблиц

-- Таблица ролей пользователей
CREATE TABLE "role" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT NOT NULL,
    "django_group_id" BIGINT NULL REFERENCES "auth_group"("id") ON DELETE SET NULL
);

-- Таблица разрешений
CREATE TABLE "permission" (
    "id" BIGSERIAL PRIMARY KEY,
    "code_name" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT NOT NULL
);

-- Связь ролей и разрешений
CREATE TABLE "role_permission" (
    "id" BIGSERIAL PRIMARY KEY,
    "role_id" BIGINT NOT NULL REFERENCES "role"("id") ON DELETE CASCADE,
    "permission_id" BIGINT NOT NULL REFERENCES "permission"("id") ON DELETE CASCADE,
    UNIQUE("role_id", "permission_id")
);

-- Таблица аккаунтов пользователей
CREATE TABLE "auth_account" (
    "id" BIGSERIAL PRIMARY KEY,
    "first_name" VARCHAR(255) NOT NULL,
    "last_name" VARCHAR(255) NOT NULL,
    "phone" VARCHAR(20) NOT NULL UNIQUE,
    "django_user_id" BIGINT NOT NULL REFERENCES "auth_user"("id") ON DELETE CASCADE
);

-- Таблица персонала
CREATE TABLE "staff" (
    "id" BIGSERIAL PRIMARY KEY,
    "user_id" BIGINT NOT NULL REFERENCES "auth_account"("id") ON DELETE CASCADE UNIQUE,
    "role_id" BIGINT NOT NULL REFERENCES "role"("id") ON DELETE CASCADE,
    "description" TEXT NOT NULL,
    "photo" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "is_archived" BOOLEAN NOT NULL DEFAULT FALSE,
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL REFERENCES "staff"("id") ON DELETE SET NULL
);

-- Таблица родителей
CREATE TABLE "parent" (
    "id" BIGSERIAL PRIMARY KEY,
    "user_id" BIGINT NULL REFERENCES "auth_account"("id") ON DELETE CASCADE UNIQUE,
    "photo" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "is_archived" BOOLEAN NOT NULL DEFAULT FALSE,
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL REFERENCES "staff"("id") ON DELETE SET NULL,
    "role_id" BIGINT NOT NULL REFERENCES "role"("id") ON DELETE CASCADE
);

-- Таблица спортсменов
CREATE TABLE "athlete" (
    "id" BIGSERIAL PRIMARY KEY,
    "user_id" BIGINT NOT NULL REFERENCES "auth_account"("id") ON DELETE CASCADE UNIQUE,
    "birth_date" DATE NOT NULL,
    "photo" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "is_archived" BOOLEAN NOT NULL DEFAULT FALSE,
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL REFERENCES "staff"("id") ON DELETE SET NULL,
    "role_id" BIGINT NOT NULL REFERENCES "role"("id") ON DELETE CASCADE
);

-- Таблица тренировочных групп
CREATE TABLE "training_group" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "age_min" INTEGER NOT NULL DEFAULT 0,
    "age_max" INTEGER NOT NULL DEFAULT 18,
    "staff_id" BIGINT NULL REFERENCES "staff"("id") ON DELETE SET NULL,
    "max_athletes" INTEGER NOT NULL DEFAULT 20,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "is_archived" BOOLEAN NOT NULL DEFAULT FALSE,
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL REFERENCES "staff"("id") ON DELETE SET NULL
);

-- Связь спортсменов и тренировочных групп
CREATE TABLE "athlete_training_group" (
    "id" BIGSERIAL PRIMARY KEY,
    "athlete_id" BIGINT NOT NULL REFERENCES "athlete"("id") ON DELETE CASCADE,
    "training_group_id" BIGINT NOT NULL REFERENCES "training_group"("id") ON DELETE CASCADE,
    UNIQUE("athlete_id", "training_group_id")
);

-- Связь спортсменов и родителей
CREATE TABLE "athlete_parent" (
    "id" BIGSERIAL PRIMARY KEY,
    "athlete_id" BIGINT NOT NULL REFERENCES "athlete"("id") ON DELETE CASCADE,
    "parent_id" BIGINT NOT NULL REFERENCES "parent"("id") ON DELETE CASCADE,
    UNIQUE("athlete_id", "parent_id")
);

-- Таблица способов оплаты
CREATE TABLE "payment_method" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE
);

-- Таблица платежей
CREATE TABLE "payment" (
    "id" BIGSERIAL PRIMARY KEY,
    "athlete_id" BIGINT NOT NULL REFERENCES "athlete"("id") ON DELETE CASCADE,
    "training_group_id" BIGINT NOT NULL REFERENCES "training_group"("id") ON DELETE CASCADE,
    "payer_id" BIGINT NOT NULL REFERENCES "auth_account"("id") ON DELETE CASCADE,
    "amount" DECIMAL(8, 2) NOT NULL,
    "payment_method_id" BIGINT NOT NULL REFERENCES "payment_method"("id") ON DELETE CASCADE,
    "comment" TEXT NOT NULL,
    "billing_period_start" DATE NOT NULL,
    "billing_period_end" DATE NOT NULL,
    "paid_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL DEFAULT NOW(),
    "is_paid" BOOLEAN NOT NULL DEFAULT FALSE,
    "invoice_number" VARCHAR(255) NOT NULL UNIQUE,
    "created_by" BIGINT NOT NULL REFERENCES "auth_account"("id") ON DELETE CASCADE,
    "is_archived" BOOLEAN NOT NULL DEFAULT FALSE,
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL REFERENCES "staff"("id") ON DELETE SET NULL
);

-- Таблица типов документов
CREATE TABLE "document_type" (
    "id" BIGSERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL UNIQUE
);

-- Таблица документов
CREATE TABLE "document" (
    "id" BIGSERIAL PRIMARY KEY,
    "file" VARCHAR(255) NOT NULL,
    "file_type" VARCHAR(255) NOT NULL,
    "file_size" INTEGER NOT NULL,
    "document_type_id" BIGINT NOT NULL REFERENCES "document_type"("id") ON DELETE CASCADE,
    "content_type_id" BIGINT NOT NULL REFERENCES "django_content_type"("id") ON DELETE CASCADE,
    "object_id" BIGINT NOT NULL,
    "uploaded_by" BIGINT NULL REFERENCES "auth_account"("id") ON DELETE SET NULL,
    "uploaded_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    "is_private" BOOLEAN NOT NULL DEFAULT FALSE,
    "comment" TEXT NOT NULL,
    "is_archived" BOOLEAN NOT NULL DEFAULT FALSE,
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL REFERENCES "staff"("id") ON DELETE SET NULL
);

-- Таблица аудита
CREATE TABLE "audit_record" (
    "id" BIGSERIAL PRIMARY KEY,
    "user_id" BIGINT NOT NULL REFERENCES "auth_account"("id") ON DELETE CASCADE,
    "action" VARCHAR(255) NOT NULL,
    "content_type_id" BIGINT NOT NULL REFERENCES "django_content_type"("id") ON DELETE CASCADE,
    "object_id" BIGINT NOT NULL,
    "timestamp" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    "details" TEXT NOT NULL
);

-- Таблица тренировочных сессий
CREATE TABLE "training_session" (
    "id" BIGSERIAL PRIMARY KEY,
    "training_group_id" BIGINT NOT NULL REFERENCES "training_group"("id") ON DELETE CASCADE,
    "date" DATE NOT NULL,
    "start_time" TIME(0) WITHOUT TIME ZONE NOT NULL,
    "end_time" TIME(0) WITHOUT TIME ZONE NOT NULL,
    "is_closed" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    "is_canceled" BOOLEAN NOT NULL DEFAULT FALSE,
    "canceled_by" BIGINT NULL REFERENCES "staff"("id") ON DELETE SET NULL,
    "canceled_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL
);

-- Таблица расписания групп
CREATE TABLE "group_schedule" (
    "id" BIGSERIAL PRIMARY KEY,
    "training_group_id" BIGINT NOT NULL REFERENCES "training_group"("id") ON DELETE CASCADE,
    "weekday" INTEGER NOT NULL,
    "start_time" TIME(0) WITHOUT TIME ZONE NOT NULL,
    "end_time" TIME(0) WITHOUT TIME ZONE NOT NULL,
    UNIQUE("training_group_id", "weekday", "start_time")
);

-- Таблица записей посещаемости
CREATE TABLE "attendance_record" (
    "id" BIGSERIAL PRIMARY KEY,
    "athlete_id" BIGINT NOT NULL REFERENCES "athlete"("id") ON DELETE CASCADE,
    "session_id" BIGINT NOT NULL REFERENCES "training_session"("id") ON DELETE CASCADE,
    "was_present" BOOLEAN NOT NULL,
    "marked_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    "marked_by" BIGINT NOT NULL REFERENCES "staff"("id") ON DELETE CASCADE,
    UNIQUE("athlete_id", "session_id")
);

-- Создание индексов для оптимизации

-- Индексы для таблицы staff
CREATE INDEX "staff_role_id_index" ON "staff"("role_id");
CREATE INDEX "staff_archived_by_index" ON "staff"("archived_by");

-- Индексы для таблицы parent
CREATE INDEX "parent_archived_by_index" ON "parent"("archived_by");
CREATE INDEX "parent_role_id_index" ON "parent"("role_id");

-- Индексы для таблицы athlete
CREATE INDEX "athlete_archived_by_index" ON "athlete"("archived_by");
CREATE INDEX "athlete_role_id_index" ON "athlete"("role_id");

-- Индексы для таблицы training_group
CREATE INDEX "training_group_age_min_index" ON "training_group"("age_min");
CREATE INDEX "training_group_age_max_index" ON "training_group"("age_max");
CREATE INDEX "training_group_staff_id_index" ON "training_group"("staff_id");
CREATE INDEX "training_group_archived_by_index" ON "training_group"("archived_by");

-- Индексы для таблицы athlete_training_group
CREATE INDEX "athlete_training_group_athlete_id_index" ON "athlete_training_group"("athlete_id");
CREATE INDEX "athlete_training_group_training_group_id_index" ON "athlete_training_group"("training_group_id");

-- Индексы для таблицы athlete_parent
CREATE INDEX "athlete_parent_athlete_id_index" ON "athlete_parent"("athlete_id");
CREATE INDEX "athlete_parent_parent_id_index" ON "athlete_parent"("parent_id");

-- Индексы для таблицы payment
CREATE INDEX "payment_athlete_id_index" ON "payment"("athlete_id");
CREATE INDEX "payment_training_group_id_index" ON "payment"("training_group_id");
CREATE INDEX "payment_payer_id_index" ON "payment"("payer_id");
CREATE INDEX "payment_payment_method_id_index" ON "payment"("payment_method_id");
CREATE INDEX "payment_paid_at_index" ON "payment"("paid_at");
CREATE INDEX "payment_created_by_index" ON "payment"("created_by");
CREATE INDEX "payment_archived_by_index" ON "payment"("archived_by");

-- Индексы для таблицы document
CREATE INDEX "document_document_type_id_index" ON "document"("document_type_id");
CREATE INDEX "document_content_type_id_index" ON "document"("content_type_id");
CREATE INDEX "document_object_id_index" ON "document"("object_id");
CREATE INDEX "document_uploaded_by_index" ON "document"("uploaded_by");
CREATE INDEX "document_archived_by_index" ON "document"("archived_by");
CREATE INDEX "document_content_type_id_object_id_index" ON "document"("content_type_id", "object_id");

-- Индексы для таблицы audit_record
CREATE INDEX "audit_record_user_id_index" ON "audit_record"("user_id");
CREATE INDEX "audit_record_content_type_id_object_id_index" ON "audit_record"("content_type_id", "object_id");

-- Индексы для таблицы training_session
CREATE INDEX "training_session_training_group_id_index" ON "training_session"("training_group_id");
CREATE INDEX "training_session_date_index" ON "training_session"("date");
CREATE INDEX "training_session_canceled_by_index" ON "training_session"("canceled_by");

-- Индексы для таблицы group_schedule
CREATE INDEX "group_schedule_training_group_id_index" ON "group_schedule"("training_group_id");
CREATE INDEX "group_schedule_weekday_index" ON "group_schedule"("weekday");
CREATE INDEX "group_schedule_start_time_index" ON "group_schedule"("start_time");

-- Индексы для таблицы attendance_record
CREATE INDEX "attendance_record_athlete_id_index" ON "attendance_record"("athlete_id");
CREATE INDEX "attendance_record_session_id_index" ON "attendance_record"("session_id");
CREATE INDEX "attendance_record_marked_by_index" ON "attendance_record"("marked_by");

-- Индексы для таблицы role_permission
CREATE INDEX "role_permission_role_id_index" ON "role_permission"("role_id");
CREATE INDEX "role_permission_permission_id_index" ON "role_permission"("permission_id");

-- Вставка базовых данных

-- Базовые роли
INSERT INTO "role" ("name", "description") VALUES
('Администратор', 'Полный доступ к системе'),
('Тренер', 'Управление группами и спортсменами'),
('Родитель', 'Доступ к информации о ребенке'),
('Спортсмен', 'Базовый доступ к системе');

-- Базовые разрешения
INSERT INTO "permission" ("code_name", "description") VALUES
('view_athletes', 'Просмотр спортсменов'),
('edit_athletes', 'Редактирование спортсменов'),
('view_payments', 'Просмотр платежей'),
('edit_payments', 'Редактирование платежей'),
('view_groups', 'Просмотр групп'),
('edit_groups', 'Редактирование групп'),
('view_documents', 'Просмотр документов'),
('edit_documents', 'Редактирование документов');

-- Связи ролей и разрешений
INSERT INTO "role_permission" ("role_id", "permission_id") VALUES
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), -- Администратор
(2, 1), (2, 2), (2, 5), (2, 6), (2, 7), -- Тренер
(3, 1), (3, 3), (3, 5), (3, 7), -- Родитель
(4, 1), (4, 5); -- Спортсмен

-- Базовые способы оплаты
INSERT INTO "payment_method" ("name", "is_active") VALUES
('Наличные', TRUE),
('Банковская карта', TRUE),
('Безналичный расчет', TRUE);

-- Базовые типы документов
INSERT INTO "document_type" ("name") VALUES
('Медицинская справка'),
('Согласие на обработку данных'),
('Договор'),
('Фотография'),
('Сертификат'); 
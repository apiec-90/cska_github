-- ===========================================
-- ПОЛНАЯ СХЕМА БАЗЫ ДАННЫХ CSKA ДЛЯ POSTGRESQL
-- Включает Django таблицы и кастомные таблицы
-- ===========================================

-- DJANGO ТАБЛИЦЫ
-- ===========================================

-- Таблица: auth_account
CREATE TABLE auth_account (
    id INTEGER NOT NULL PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    phone VARCHAR NOT NULL,
    is_active TEXT NOT NULL,
    is_archived TEXT NOT NULL,
    archived_at TIMESTAMP,
    django_user_id INTEGER,
    archived_by_id INTEGER,
    role_id INTEGER
);

-- Таблица: auth_group
CREATE TABLE auth_group (
    id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR NOT NULL
);

-- Таблица: auth_group_permissions
CREATE TABLE auth_group_permissions (
    id INTEGER NOT NULL PRIMARY KEY,
    group_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL
);

-- Таблица: auth_permission
CREATE TABLE auth_permission (
    id INTEGER NOT NULL PRIMARY KEY,
    content_type_id INTEGER NOT NULL,
    codename VARCHAR NOT NULL,
    name VARCHAR NOT NULL
);

-- Таблица: auth_user
CREATE TABLE auth_user (
    id INTEGER NOT NULL PRIMARY KEY,
    password VARCHAR NOT NULL,
    last_login TIMESTAMP,
    is_superuser TEXT NOT NULL,
    username VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    is_staff TEXT NOT NULL,
    is_active TEXT NOT NULL,
    date_joined TIMESTAMP NOT NULL,
    first_name VARCHAR NOT NULL
);

-- Таблица: auth_user_groups
CREATE TABLE auth_user_groups (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL
);

-- Таблица: auth_user_user_permissions
CREATE TABLE auth_user_user_permissions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL
);

-- Таблица: django_admin_log
CREATE TABLE django_admin_log (
    id INTEGER NOT NULL PRIMARY KEY,
    object_id TEXT,
    object_repr VARCHAR NOT NULL,
    action_flag TEXT NOT NULL,
    change_message TEXT NOT NULL,
    content_type_id INTEGER,
    user_id INTEGER NOT NULL,
    action_time TIMESTAMP NOT NULL
);

-- Таблица: django_content_type
CREATE TABLE django_content_type (
    id INTEGER NOT NULL PRIMARY KEY,
    app_label VARCHAR NOT NULL,
    model VARCHAR NOT NULL
);

-- Таблица: django_migrations
CREATE TABLE django_migrations (
    id INTEGER NOT NULL PRIMARY KEY,
    app VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    applied TIMESTAMP NOT NULL
);

-- Таблица: django_session
CREATE TABLE django_session (
    session_key VARCHAR NOT NULL PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date TIMESTAMP NOT NULL
);

-- КАСТОМНЫЕ ТАБЛИЦЫ
-- ===========================================

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

-- ИНДЕКСЫ
-- ===========================================

-- Индекс: athlete_archived_by_id_91bacebf
CREATE INDEX "athlete_archived_by_id_91bacebf" ON "athlete" ("archived_by_id");

-- Индекс: athlete_parent_athlete_id_6ea417e9
CREATE INDEX "athlete_parent_athlete_id_6ea417e9" ON "athlete_parent" ("athlete_id");

-- Индекс: athlete_parent_athlete_id_parent_id_923dc76b_uniq
CREATE UNIQUE INDEX "athlete_parent_athlete_id_parent_id_923dc76b_uniq" ON "athlete_parent" ("athlete_id", "parent_id");

-- Индекс: athlete_parent_parent_id_1ac812e9
CREATE INDEX "athlete_parent_parent_id_1ac812e9" ON "athlete_parent" ("parent_id");

-- Индекс: athlete_training_group_athlete_id_28ff5a2c
CREATE INDEX "athlete_training_group_athlete_id_28ff5a2c" ON "athlete_training_group" ("athlete_id");

-- Индекс: athlete_training_group_athlete_id_training_group_id_d5ba9abb_uniq
CREATE UNIQUE INDEX "athlete_training_group_athlete_id_training_group_id_d5ba9abb_uniq" ON "athlete_training_group" ("athlete_id", "training_group_id");

-- Индекс: athlete_training_group_training_group_id_b3d8ecfa
CREATE INDEX "athlete_training_group_training_group_id_b3d8ecfa" ON "athlete_training_group" ("training_group_id");

-- Индекс: attendance_record_athlete_id_b4f973a5
CREATE INDEX "attendance_record_athlete_id_b4f973a5" ON "attendance_record" ("athlete_id");

-- Индекс: attendance_record_marked_by_id_f018e51e
CREATE INDEX "attendance_record_marked_by_id_f018e51e" ON "attendance_record" ("marked_by_id");

-- Индекс: attendance_record_training_session_id_7d78dd6a
CREATE INDEX "attendance_record_training_session_id_7d78dd6a" ON "attendance_record" ("training_session_id");

-- Индекс: attendance_record_training_session_id_athlete_id_519ca15a_uniq
CREATE UNIQUE INDEX "attendance_record_training_session_id_athlete_id_519ca15a_uniq" ON "attendance_record" ("training_session_id", "athlete_id");

-- Индекс: audit_record_user_id_86030b62
CREATE INDEX "audit_record_user_id_86030b62" ON "audit_record" ("user_id");

-- Индекс: auth_account_archived_by_id_7630605f
CREATE INDEX "auth_account_archived_by_id_7630605f" ON "auth_account" ("archived_by_id");

-- Индекс: auth_account_role_id_c0839a12
CREATE INDEX "auth_account_role_id_c0839a12" ON "auth_account" ("role_id");

-- Индекс: auth_group_permissions_group_id_b120cbf9
CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");

-- Индекс: auth_group_permissions_group_id_permission_id_0cd325b0_uniq
CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");

-- Индекс: auth_group_permissions_permission_id_84c5c92e
CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");

-- Индекс: auth_permission_content_type_id_2f476e4b
CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");

-- Индекс: auth_permission_content_type_id_codename_01ab375a_uniq
CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");

-- Индекс: auth_user_groups_group_id_97559544
CREATE INDEX "auth_user_groups_group_id_97559544" ON "auth_user_groups" ("group_id");

-- Индекс: auth_user_groups_user_id_6a12ed8b
CREATE INDEX "auth_user_groups_user_id_6a12ed8b" ON "auth_user_groups" ("user_id");

-- Индекс: auth_user_groups_user_id_group_id_94350c0c_uniq
CREATE UNIQUE INDEX "auth_user_groups_user_id_group_id_94350c0c_uniq" ON "auth_user_groups" ("user_id", "group_id");

-- Индекс: auth_user_user_permissions_permission_id_1fbb5f2c
CREATE INDEX "auth_user_user_permissions_permission_id_1fbb5f2c" ON "auth_user_user_permissions" ("permission_id");

-- Индекс: auth_user_user_permissions_user_id_a95ead1b
CREATE INDEX "auth_user_user_permissions_user_id_a95ead1b" ON "auth_user_user_permissions" ("user_id");

-- Индекс: auth_user_user_permissions_user_id_permission_id_14a6b632_uniq
CREATE UNIQUE INDEX "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq" ON "auth_user_user_permissions" ("user_id", "permission_id");

-- Индекс: django_admin_log_content_type_id_c4bce8eb
CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");

-- Индекс: django_admin_log_user_id_c564eba6
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");

-- Индекс: django_content_type_app_label_model_76bd3d3b_uniq
CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");

-- Индекс: django_session_expire_date_a5c62663
CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");

-- Индекс: document_content_type_id_19300afd
CREATE INDEX "document_content_type_id_19300afd" ON "document" ("content_type_id");

-- Индекс: document_document_type_id_7662c031
CREATE INDEX "document_document_type_id_7662c031" ON "document" ("document_type_id");

-- Индекс: group_schedule_training_group_id_6809ccc0
CREATE INDEX "group_schedule_training_group_id_6809ccc0" ON "group_schedule" ("training_group_id");

-- Индекс: group_schedule_training_group_id_day_of_week_8462c093_uniq
CREATE UNIQUE INDEX "group_schedule_training_group_id_day_of_week_8462c093_uniq" ON "group_schedule" ("training_group_id", "day_of_week");

-- Индекс: parent_archived_by_id_45eccc88
CREATE INDEX "parent_archived_by_id_45eccc88" ON "parent" ("archived_by_id");

-- Индекс: payment_athlete_id_f79b8aba
CREATE INDEX "payment_athlete_id_f79b8aba" ON "payment" ("athlete_id");

-- Индекс: payment_payment_method_id_47847947
CREATE INDEX "payment_payment_method_id_47847947" ON "payment" ("payment_method_id");

-- Индекс: role_permission_permission_id_ee9c5982
CREATE INDEX "role_permission_permission_id_ee9c5982" ON "role_permission" ("permission_id");

-- Индекс: role_permission_role_id_877a80a4
CREATE INDEX "role_permission_role_id_877a80a4" ON "role_permission" ("role_id");

-- Индекс: role_permission_role_id_permission_id_0a48a767_uniq
CREATE UNIQUE INDEX "role_permission_role_id_permission_id_0a48a767_uniq" ON "role_permission" ("role_id", "permission_id");

-- Индекс: staff_archived_by_id_29ee9c9b
CREATE INDEX "staff_archived_by_id_29ee9c9b" ON "staff" ("archived_by_id");

-- Индекс: staff_role_id_f8da7ae2
CREATE INDEX "staff_role_id_f8da7ae2" ON "staff" ("role_id");

-- Индекс: training_group_archived_by_a1999f2c
CREATE INDEX "training_group_archived_by_a1999f2c" ON "training_group" ("archived_by");

-- Индекс: training_group_staff_id_1d0bb416
CREATE INDEX "training_group_staff_id_1d0bb416" ON "training_group" ("staff_id");

-- Индекс: training_session_training_group_id_3d430daa
CREATE INDEX "training_session_training_group_id_3d430daa" ON "training_session" ("training_group_id");

-- ПОСЛЕДОВАТЕЛЬНОСТИ
-- ===========================================

CREATE SEQUENCE IF NOT EXISTS athlete_id_seq;
ALTER TABLE athlete ALTER COLUMN id SET DEFAULT nextval('athlete_id_seq');
ALTER SEQUENCE athlete_id_seq OWNED BY athlete.id;

CREATE SEQUENCE IF NOT EXISTS athlete_parent_id_seq;
ALTER TABLE athlete_parent ALTER COLUMN id SET DEFAULT nextval('athlete_parent_id_seq');
ALTER SEQUENCE athlete_parent_id_seq OWNED BY athlete_parent.id;

CREATE SEQUENCE IF NOT EXISTS athlete_training_group_id_seq;
ALTER TABLE athlete_training_group ALTER COLUMN id SET DEFAULT nextval('athlete_training_group_id_seq');
ALTER SEQUENCE athlete_training_group_id_seq OWNED BY athlete_training_group.id;

CREATE SEQUENCE IF NOT EXISTS attendance_record_id_seq;
ALTER TABLE attendance_record ALTER COLUMN id SET DEFAULT nextval('attendance_record_id_seq');
ALTER SEQUENCE attendance_record_id_seq OWNED BY attendance_record.id;

CREATE SEQUENCE IF NOT EXISTS audit_record_id_seq;
ALTER TABLE audit_record ALTER COLUMN id SET DEFAULT nextval('audit_record_id_seq');
ALTER SEQUENCE audit_record_id_seq OWNED BY audit_record.id;

CREATE SEQUENCE IF NOT EXISTS auth_account_id_seq;
ALTER TABLE auth_account ALTER COLUMN id SET DEFAULT nextval('auth_account_id_seq');
ALTER SEQUENCE auth_account_id_seq OWNED BY auth_account.id;

CREATE SEQUENCE IF NOT EXISTS auth_group_id_seq;
ALTER TABLE auth_group ALTER COLUMN id SET DEFAULT nextval('auth_group_id_seq');
ALTER SEQUENCE auth_group_id_seq OWNED BY auth_group.id;

CREATE SEQUENCE IF NOT EXISTS auth_group_permissions_id_seq;
ALTER TABLE auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('auth_group_permissions_id_seq');
ALTER SEQUENCE auth_group_permissions_id_seq OWNED BY auth_group_permissions.id;

CREATE SEQUENCE IF NOT EXISTS auth_permission_id_seq;
ALTER TABLE auth_permission ALTER COLUMN id SET DEFAULT nextval('auth_permission_id_seq');
ALTER SEQUENCE auth_permission_id_seq OWNED BY auth_permission.id;

CREATE SEQUENCE IF NOT EXISTS auth_user_id_seq;
ALTER TABLE auth_user ALTER COLUMN id SET DEFAULT nextval('auth_user_id_seq');
ALTER SEQUENCE auth_user_id_seq OWNED BY auth_user.id;

CREATE SEQUENCE IF NOT EXISTS auth_user_groups_id_seq;
ALTER TABLE auth_user_groups ALTER COLUMN id SET DEFAULT nextval('auth_user_groups_id_seq');
ALTER SEQUENCE auth_user_groups_id_seq OWNED BY auth_user_groups.id;

CREATE SEQUENCE IF NOT EXISTS auth_user_user_permissions_id_seq;
ALTER TABLE auth_user_user_permissions ALTER COLUMN id SET DEFAULT nextval('auth_user_user_permissions_id_seq');
ALTER SEQUENCE auth_user_user_permissions_id_seq OWNED BY auth_user_user_permissions.id;

CREATE SEQUENCE IF NOT EXISTS django_admin_log_id_seq;
ALTER TABLE django_admin_log ALTER COLUMN id SET DEFAULT nextval('django_admin_log_id_seq');
ALTER SEQUENCE django_admin_log_id_seq OWNED BY django_admin_log.id;

CREATE SEQUENCE IF NOT EXISTS django_content_type_id_seq;
ALTER TABLE django_content_type ALTER COLUMN id SET DEFAULT nextval('django_content_type_id_seq');
ALTER SEQUENCE django_content_type_id_seq OWNED BY django_content_type.id;

CREATE SEQUENCE IF NOT EXISTS django_migrations_id_seq;
ALTER TABLE django_migrations ALTER COLUMN id SET DEFAULT nextval('django_migrations_id_seq');
ALTER SEQUENCE django_migrations_id_seq OWNED BY django_migrations.id;

CREATE SEQUENCE IF NOT EXISTS django_session_id_seq;
ALTER TABLE django_session ALTER COLUMN id SET DEFAULT nextval('django_session_id_seq');
ALTER SEQUENCE django_session_id_seq OWNED BY django_session.id;

CREATE SEQUENCE IF NOT EXISTS document_id_seq;
ALTER TABLE document ALTER COLUMN id SET DEFAULT nextval('document_id_seq');
ALTER SEQUENCE document_id_seq OWNED BY document.id;

CREATE SEQUENCE IF NOT EXISTS document_type_id_seq;
ALTER TABLE document_type ALTER COLUMN id SET DEFAULT nextval('document_type_id_seq');
ALTER SEQUENCE document_type_id_seq OWNED BY document_type.id;

CREATE SEQUENCE IF NOT EXISTS group_schedule_id_seq;
ALTER TABLE group_schedule ALTER COLUMN id SET DEFAULT nextval('group_schedule_id_seq');
ALTER SEQUENCE group_schedule_id_seq OWNED BY group_schedule.id;

CREATE SEQUENCE IF NOT EXISTS parent_id_seq;
ALTER TABLE parent ALTER COLUMN id SET DEFAULT nextval('parent_id_seq');
ALTER SEQUENCE parent_id_seq OWNED BY parent.id;

CREATE SEQUENCE IF NOT EXISTS payment_id_seq;
ALTER TABLE payment ALTER COLUMN id SET DEFAULT nextval('payment_id_seq');
ALTER SEQUENCE payment_id_seq OWNED BY payment.id;

CREATE SEQUENCE IF NOT EXISTS payment_method_id_seq;
ALTER TABLE payment_method ALTER COLUMN id SET DEFAULT nextval('payment_method_id_seq');
ALTER SEQUENCE payment_method_id_seq OWNED BY payment_method.id;

CREATE SEQUENCE IF NOT EXISTS role_id_seq;
ALTER TABLE role ALTER COLUMN id SET DEFAULT nextval('role_id_seq');
ALTER SEQUENCE role_id_seq OWNED BY role.id;

CREATE SEQUENCE IF NOT EXISTS role_permission_id_seq;
ALTER TABLE role_permission ALTER COLUMN id SET DEFAULT nextval('role_permission_id_seq');
ALTER SEQUENCE role_permission_id_seq OWNED BY role_permission.id;

CREATE SEQUENCE IF NOT EXISTS sqlite_sequence_id_seq;
ALTER TABLE sqlite_sequence ALTER COLUMN id SET DEFAULT nextval('sqlite_sequence_id_seq');
ALTER SEQUENCE sqlite_sequence_id_seq OWNED BY sqlite_sequence.id;

CREATE SEQUENCE IF NOT EXISTS staff_id_seq;
ALTER TABLE staff ALTER COLUMN id SET DEFAULT nextval('staff_id_seq');
ALTER SEQUENCE staff_id_seq OWNED BY staff.id;

CREATE SEQUENCE IF NOT EXISTS training_group_id_seq;
ALTER TABLE training_group ALTER COLUMN id SET DEFAULT nextval('training_group_id_seq');
ALTER SEQUENCE training_group_id_seq OWNED BY training_group.id;

CREATE SEQUENCE IF NOT EXISTS training_session_id_seq;
ALTER TABLE training_session ALTER COLUMN id SET DEFAULT nextval('training_session_id_seq');
ALTER SEQUENCE training_session_id_seq OWNED BY training_session.id;

-- БАЗОВЫЕ ДАННЫЕ
-- ===========================================

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
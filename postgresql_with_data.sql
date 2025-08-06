-- ===========================================
-- ПОЛНАЯ БАЗА ДАННЫХ CSKA ДЛЯ POSTGRESQL
-- Включает схему и данные
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

-- ДАННЫЕ
-- ===========================================

-- Данные таблицы: auth_account
INSERT INTO auth_account (id, first_name, last_name, phone, is_active, is_archived, archived_at, django_user_id, archived_by_id, role_id) VALUES
    (1, 'Иван', 'Тренеров', '+7-999-123-45-67', 1, 0, NULL, NULL, NULL, 2),
    (2, '', '', '+7900admin1234', 1, 0, NULL, 1, NULL, 1),
    (3, 'Trainer', 'Тестовый', '+7900trainer1234', 1, 0, NULL, 3, NULL, 2),
    (4, 'Parent', 'Тестовый', '+7900parent1234', 1, 0, NULL, 4, NULL, 3);

-- Данные таблицы: auth_group
INSERT INTO auth_group (id, name) VALUES
    (2, 'Администратор'),
    (3, 'Тренер'),
    (4, 'Родитель'),
    (5, 'Спортсмен');

-- Данные таблицы: auth_permission
INSERT INTO auth_permission (id, content_type_id, codename, name) VALUES
    (1, 1, 'add_logentry', 'Can add log entry'),
    (2, 1, 'change_logentry', 'Can change log entry'),
    (3, 1, 'delete_logentry', 'Can delete log entry'),
    (4, 1, 'view_logentry', 'Can view log entry'),
    (5, 2, 'add_permission', 'Can add permission'),
    (6, 2, 'change_permission', 'Can change permission'),
    (7, 2, 'delete_permission', 'Can delete permission'),
    (8, 2, 'view_permission', 'Can view permission'),
    (9, 3, 'add_group', 'Can add group'),
    (10, 3, 'change_group', 'Can change group'),
    (11, 3, 'delete_group', 'Can delete group'),
    (12, 3, 'view_group', 'Can view group'),
    (13, 4, 'add_user', 'Can add user'),
    (14, 4, 'change_user', 'Can change user'),
    (15, 4, 'delete_user', 'Can delete user'),
    (16, 4, 'view_user', 'Can view user'),
    (17, 5, 'add_contenttype', 'Can add content type'),
    (18, 5, 'change_contenttype', 'Can change content type'),
    (19, 5, 'delete_contenttype', 'Can delete content type'),
    (20, 5, 'view_contenttype', 'Can view content type'),
    (21, 6, 'add_session', 'Can add session'),
    (22, 6, 'change_session', 'Can change session'),
    (23, 6, 'delete_session', 'Can delete session'),
    (24, 6, 'view_session', 'Can view session'),
    (25, 7, 'add_documenttype', 'Can add Тип документа'),
    (26, 7, 'change_documenttype', 'Can change Тип документа'),
    (27, 7, 'delete_documenttype', 'Can delete Тип документа'),
    (28, 7, 'view_documenttype', 'Can view Тип документа'),
    (29, 8, 'add_paymentmethod', 'Can add Способ оплаты'),
    (30, 8, 'change_paymentmethod', 'Can change Способ оплаты'),
    (31, 8, 'delete_paymentmethod', 'Can delete Способ оплаты'),
    (32, 8, 'view_paymentmethod', 'Can view Способ оплаты'),
    (33, 9, 'add_permission', 'Can add Разрешение'),
    (34, 9, 'change_permission', 'Can change Разрешение'),
    (35, 9, 'delete_permission', 'Can delete Разрешение'),
    (36, 9, 'view_permission', 'Can view Разрешение'),
    (37, 10, 'add_role', 'Can add Роль'),
    (38, 10, 'change_role', 'Can change Роль'),
    (39, 10, 'delete_role', 'Can delete Роль'),
    (40, 10, 'view_role', 'Can view Роль'),
    (41, 11, 'add_authaccount', 'Can add Аккаунт пользователя'),
    (42, 11, 'change_authaccount', 'Can change Аккаунт пользователя'),
    (43, 11, 'delete_authaccount', 'Can delete Аккаунт пользователя'),
    (44, 11, 'view_authaccount', 'Can view Аккаунт пользователя'),
    (45, 12, 'add_auditrecord', 'Can add Запись аудита'),
    (46, 12, 'change_auditrecord', 'Can change Запись аудита'),
    (47, 12, 'delete_auditrecord', 'Can delete Запись аудита'),
    (48, 12, 'view_auditrecord', 'Can view Запись аудита'),
    (49, 13, 'add_athlete', 'Can add Спортсмен'),
    (50, 13, 'change_athlete', 'Can change Спортсмен'),
    (51, 13, 'delete_athlete', 'Can delete Спортсмен'),
    (52, 13, 'view_athlete', 'Can view Спортсмен'),
    (53, 14, 'add_document', 'Can add Документ'),
    (54, 14, 'change_document', 'Can change Документ'),
    (55, 14, 'delete_document', 'Can delete Документ'),
    (56, 14, 'view_document', 'Can view Документ'),
    (57, 15, 'add_payment', 'Can add Платеж'),
    (58, 15, 'change_payment', 'Can change Платеж'),
    (59, 15, 'delete_payment', 'Can delete Платеж'),
    (60, 15, 'view_payment', 'Can view Платеж'),
    (61, 16, 'add_staff', 'Can add Сотрудник'),
    (62, 16, 'change_staff', 'Can change Сотрудник'),
    (63, 16, 'delete_staff', 'Can delete Сотрудник'),
    (64, 16, 'view_staff', 'Can view Сотрудник'),
    (65, 17, 'add_parent', 'Can add Родитель'),
    (66, 17, 'change_parent', 'Can change Родитель'),
    (67, 17, 'delete_parent', 'Can delete Родитель'),
    (68, 17, 'view_parent', 'Can view Родитель'),
    (69, 18, 'add_traininggroup', 'Can add Тренировочная группа'),
    (70, 18, 'change_traininggroup', 'Can change Тренировочная группа'),
    (71, 18, 'delete_traininggroup', 'Can delete Тренировочная группа'),
    (72, 18, 'view_traininggroup', 'Can view Тренировочная группа'),
    (73, 19, 'add_trainingsession', 'Can add Тренировочная сессия'),
    (74, 19, 'change_trainingsession', 'Can change Тренировочная сессия'),
    (75, 19, 'delete_trainingsession', 'Can delete Тренировочная сессия'),
    (76, 19, 'view_trainingsession', 'Can view Тренировочная сессия'),
    (77, 20, 'add_athleteparent', 'Can add Связь спортсмен-родитель'),
    (78, 20, 'change_athleteparent', 'Can change Связь спортсмен-родитель'),
    (79, 20, 'delete_athleteparent', 'Can delete Связь спортсмен-родитель'),
    (80, 20, 'view_athleteparent', 'Can view Связь спортсмен-родитель'),
    (81, 21, 'add_rolepermission', 'Can add Разрешение роли'),
    (82, 21, 'change_rolepermission', 'Can change Разрешение роли'),
    (83, 21, 'delete_rolepermission', 'Can delete Разрешение роли'),
    (84, 21, 'view_rolepermission', 'Can view Разрешение роли'),
    (85, 22, 'add_groupschedule', 'Can add Расписание группы'),
    (86, 22, 'change_groupschedule', 'Can change Расписание группы'),
    (87, 22, 'delete_groupschedule', 'Can delete Расписание группы'),
    (88, 22, 'view_groupschedule', 'Can view Расписание группы'),
    (89, 23, 'add_athletetraininggroup', 'Can add Спортсмен в группе'),
    (90, 23, 'change_athletetraininggroup', 'Can change Спортсмен в группе'),
    (91, 23, 'delete_athletetraininggroup', 'Can delete Спортсмен в группе'),
    (92, 23, 'view_athletetraininggroup', 'Can view Спортсмен в группе'),
    (93, 24, 'add_attendancerecord', 'Can add Запись посещаемости'),
    (94, 24, 'change_attendancerecord', 'Can change Запись посещаемости'),
    (95, 24, 'delete_attendancerecord', 'Can delete Запись посещаемости'),
    (96, 24, 'view_attendancerecord', 'Can view Запись посещаемости');

-- Данные таблицы: auth_user
INSERT INTO auth_user (id, password, last_login, is_superuser, username, last_name, email, is_staff, is_active, date_joined, first_name) VALUES
    (1, 'pbkdf2_sha256$1000000$K8GPZz3aRPy4XRKsGiF7k0$wqunTN7XCWqfzoLIKHZsmyBAmtxBY2dYgFl6Y4MCtfs=', '2025-08-05 20:59:45.387337', 1, 'admin', '', 'admin@example.com', 1, 1, '2025-08-05 20:57:10.056802', ''),
    (2, 'pbkdf2_sha256$1000000$KUUqt60My5jJV9zFBBjUl0$KgedkFPklyY+oybPYKmJButnbHA3GBD8xIkn73lO/3U=', NULL, 0, 'trainer_test', 'Тренеров', 'trainer@test.com', 0, 1, '2025-08-05 23:40:55.427237', 'Иван'),
    (3, 'pbkdf2_sha256$1000000$8gAlHQLeTg11kLbNx0TJ1C$qXZsP5GPheqMcUom/93LNCbBdXoTke7De63j0BOCvJw=', NULL, 0, 'trainer', 'Тестовый', 'trainer@example.com', 0, 1, '2025-08-06 10:52:13.326257', 'Trainer'),
    (4, 'pbkdf2_sha256$1000000$J5jIYOFyyrE0ie5JmHiC26$yNJkOIa6mBXQArr1HPDEaStagSyDK3/vGPC53h5t4rA=', NULL, 0, 'parent', 'Тестовый', 'parent@example.com', 0, 1, '2025-08-06 10:52:14.652932', 'Parent');

-- Данные таблицы: auth_user_groups
INSERT INTO auth_user_groups (id, user_id, group_id) VALUES
    (1, 1, 2),
    (2, 3, 3),
    (3, 4, 4);

-- Данные таблицы: django_admin_log
INSERT INTO django_admin_log (id, object_id, object_repr, action_flag, change_message, content_type_id, user_id, action_time) VALUES
    (1, '1', 'Тренер - Просмотр спортсменов', 1, '[{"added": {}}]', 21, 1, '2025-08-05 21:05:56.298475'),
    (2, '1', 'Тренер - Просмотр спортсменов', 2, '[]', 21, 1, '2025-08-05 21:06:10.810512'),
    (3, '1', 'тренер', 1, '[{"added": {}}]', 3, 1, '2025-08-05 23:13:17.578250');

-- Данные таблицы: django_content_type
INSERT INTO django_content_type (id, app_label, model) VALUES
    (1, 'admin', 'logentry'),
    (2, 'auth', 'permission'),
    (3, 'auth', 'group'),
    (4, 'auth', 'user'),
    (5, 'contenttypes', 'contenttype'),
    (6, 'sessions', 'session'),
    (7, 'core', 'documenttype'),
    (8, 'core', 'paymentmethod'),
    (9, 'core', 'permission'),
    (10, 'core', 'role'),
    (11, 'core', 'authaccount'),
    (12, 'core', 'auditrecord'),
    (13, 'core', 'athlete'),
    (14, 'core', 'document'),
    (15, 'core', 'payment'),
    (16, 'core', 'staff'),
    (17, 'core', 'parent'),
    (18, 'core', 'traininggroup'),
    (19, 'core', 'trainingsession'),
    (20, 'core', 'athleteparent'),
    (21, 'core', 'rolepermission'),
    (22, 'core', 'groupschedule'),
    (23, 'core', 'athletetraininggroup'),
    (24, 'core', 'attendancerecord');

-- Данные таблицы: django_migrations
INSERT INTO django_migrations (id, app, name, applied) VALUES
    (1, 'contenttypes', '0001_initial', '2025-08-05 20:52:07.885849'),
    (2, 'auth', '0001_initial', '2025-08-05 20:52:07.930080'),
    (3, 'admin', '0001_initial', '2025-08-05 20:52:07.970086'),
    (4, 'admin', '0002_logentry_remove_auto_add', '2025-08-05 20:52:08.019829'),
    (5, 'admin', '0003_logentry_add_action_flag_choices', '2025-08-05 20:52:08.041102'),
    (6, 'contenttypes', '0002_remove_content_type_name', '2025-08-05 20:52:08.088489'),
    (7, 'auth', '0002_alter_permission_name_max_length', '2025-08-05 20:52:08.117498'),
    (8, 'auth', '0003_alter_user_email_max_length', '2025-08-05 20:52:08.147501'),
    (9, 'auth', '0004_alter_user_username_opts', '2025-08-05 20:52:08.171732'),
    (10, 'auth', '0005_alter_user_last_login_null', '2025-08-05 20:52:08.208741'),
    (11, 'auth', '0006_require_contenttypes_0002', '2025-08-05 20:52:08.229151'),
    (12, 'auth', '0007_alter_validators_add_error_messages', '2025-08-05 20:52:08.257804'),
    (13, 'auth', '0008_alter_user_username_max_length', '2025-08-05 20:52:08.293970'),
    (14, 'auth', '0009_alter_user_last_name_max_length', '2025-08-05 20:52:08.328836'),
    (15, 'auth', '0010_alter_group_name_max_length', '2025-08-05 20:52:08.369583'),
    (16, 'auth', '0011_update_proxy_permissions', '2025-08-05 20:52:08.395596'),
    (17, 'auth', '0012_alter_user_first_name_max_length', '2025-08-05 20:52:08.431053'),
    (18, 'core', '0001_initial', '2025-08-05 20:52:08.689111'),
    (19, 'sessions', '0001_initial', '2025-08-05 20:52:08.717110'),
    (20, 'core', '0002_alter_athlete_id_alter_athleteparent_id_and_more', '2025-08-05 20:57:02.481398'),
    (21, 'core', '0003_role_permissions', '2025-08-05 22:21:37.083980'),
    (22, 'core', '0004_authaccount_role', '2025-08-05 23:05:49.653979'),
    (23, 'core', '0005_alter_rolepermission_permission_and_more', '2025-08-05 23:57:17.980639'),
    (24, 'core', '0006_role_django_group', '2025-08-06 10:50:54.565991');

-- Данные таблицы: django_session
INSERT INTO django_session (session_key, session_data, expire_date) VALUES
    ('k0iuleh3kvsv6c2roh1r48b7dn0hdhlb', '.eJxVjEEOwiAQAP_C2RC6QGE9eu8bCLAgVQNJaU_GvxuSHvQ6M5k3c_7Yizt62txK7MomdvllwcdnqkPQw9d747HVfVsDHwk_bedLo_S6ne3foPhexlapTCoAagsgTKKEmCV4MUsbIRJpgxLFDDoDKZuE0ZaslIgB46QE-3wBxIw2zA:1ujOl7:bSkVSCE5b3CWCLMDAGVjIQjruknlxVKnI2xEwhnS3wo', '2025-08-19 20:59:45.408348'),

-- Данные таблицы: document_type
INSERT INTO document_type (name, description, allowed_formats, id) VALUES
    ('Паспорт', 'Паспорт гражданина РФ', '["jpg", "jpeg", "png", "pdf"]', 1),
    ('Справка', 'Медицинская справка', '["pdf", "doc", "docx"]', 2),
    ('Фото', 'Фотография спортсмена', '["jpg", "jpeg", "png"]', 3);

-- Данные таблицы: payment_method
INSERT INTO payment_method (name, description, id) VALUES
    ('Наличные', 'Оплата наличными', 1),
    ('Банковская карта', 'Оплата банковской картой', 2),
    ('Безналичный расчет', 'Безналичный расчет', 3),
    ('Электронный кошелек', 'Оплата через электронный кошелек', 4);

-- Данные таблицы: role
INSERT INTO role (id, name, description, django_group_id) VALUES
    (1, 'Администратор', 'Полный доступ к системе', 2),
    (2, 'Тренер', 'Управление группами и спортсменами', 3),
    (3, 'Родитель', 'Просмотр информации о ребенке', 4),
    (4, 'Спортсмен', 'Просмотр своей информации', 5);

-- Данные таблицы: role_permission
INSERT INTO role_permission (id, role_id, permission_id) VALUES
    (1, 1, 41),
    (2, 1, 42),
    (3, 1, 43),
    (4, 1, 44),
    (5, 1, 61),
    (6, 1, 62),
    (7, 1, 63),
    (8, 1, 64),
    (9, 1, 49),
    (10, 1, 50),
    (11, 1, 51),
    (12, 1, 52),
    (13, 1, 69),
    (14, 1, 70),
    (15, 1, 71),
    (16, 1, 72),
    (17, 1, 57),
    (18, 1, 58),
    (19, 1, 59),
    (20, 1, 60),
    (21, 1, 53),
    (22, 1, 54),
    (23, 1, 55),
    (24, 1, 56),
    (25, 2, 49),
    (26, 2, 50),
    (27, 2, 52),
    (28, 2, 69),
    (29, 2, 70),
    (30, 2, 72),
    (31, 2, 64),
    (32, 2, 60),
    (33, 2, 56),
    (34, 3, 52),
    (35, 3, 72),
    (36, 3, 60),
    (37, 3, 56),
    (38, 4, 52),
    (39, 4, 72),
    (40, 4, 60),
    (41, 4, 56),
    (44, 1, 16),
    (45, 1, 13),
    (46, 1, 14),
    (47, 1, 15),
    (48, 2, 16),
    (49, 2, 14),
    (50, 3, 16);

-- Данные таблицы: sqlite_sequence
INSERT INTO sqlite_sequence (name, seq) VALUES
    ('django_migrations', 24),
    ('django_admin_log', 3),
    ('django_content_type', 24),
    ('auth_permission', 96),
    ('auth_group', 6),
    ('auth_user', 4),
    ('audit_record', 0),
    ('document_type', 3),
    ('document', 0),
    ('athlete_parent', 0),
    ('payment_method', 4),
    ('payment', 0),
    ('parent', 0),
    ('athlete', 0),
    ('auth_account', 4),
    ('staff', 1),
    ('training_group', 1),
    ('group_schedule', 0),
    ('athlete_training_group', 0),
    ('training_session', 0),
    ('attendance_record', 0),
    ('auth_group_permissions', 7),
    ('role_permission', 50),
    ('role', 5),
    ('auth_user_groups', 3);

-- Данные таблицы: staff
INSERT INTO staff (id, is_active, is_archived, archived_at, role_id, user_id, archived_by_id) VALUES
    (1, 1, 0, NULL, 2, 1, NULL),

-- Данные таблицы: training_group
INSERT INTO training_group (name, age_min, age_max, max_athletes, training_days, start_time, end_time, is_active, is_archived, archived_at, archived_by, staff_id, id) VALUES
    ('Младшая группа', 7, 10, 15, '[1, 3, 5]', '16:00:00', '17:30:00', 1, 0, NULL, NULL, 1, 1),

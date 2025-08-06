-- Создание базы данных для спортивной школы CSKA
CREATE DATABASE cska_sports_school;

-- Подключение к созданной базе данных
\c cska_sports_school;

-- Создание таблиц
CREATE TABLE "role" (
    "id" bigint NOT NULL,
    "name" varchar(255) NOT NULL,
    "description" text,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "permission" (
    "id" bigint NOT NULL,
    "name" varchar(255) NOT NULL,
    "code_name" varchar(255) NOT NULL,
    "description" text,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "role_permission" (
    "id" bigint NOT NULL,
    "role_id" bigint NOT NULL,
    "permission_id" bigint NOT NULL,
    "created_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "auth_account" (
    "id" bigint NOT NULL,
    "first_name" varchar(255) NOT NULL,
    "last_name" varchar(255) NOT NULL,
    "phone" varchar(20) NOT NULL,
    "django_user_id" bigint,
    "is_active" boolean DEFAULT true,
    "is_archived" boolean DEFAULT false,
    "archived_at" timestamp with time zone,
    "archived_by" bigint,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "staff" (
    "id" bigint NOT NULL,
    "user_id" bigint NOT NULL,
    "role_id" bigint NOT NULL,
    "is_active" boolean DEFAULT true,
    "is_archived" boolean DEFAULT false,
    "archived_at" timestamp with time zone,
    "archived_by" bigint,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "parent" (
    "id" bigint NOT NULL,
    "user_id" bigint NOT NULL,
    "is_active" boolean DEFAULT true,
    "is_archived" boolean DEFAULT false,
    "archived_at" timestamp with time zone,
    "archived_by" bigint,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "athlete" (
    "id" bigint NOT NULL,
    "user_id" bigint NOT NULL,
    "birth_date" date,
    "photo" varchar(255),
    "is_active" boolean DEFAULT true,
    "is_archived" boolean DEFAULT false,
    "archived_at" timestamp with time zone,
    "archived_by" bigint,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "training_group" (
    "id" bigint NOT NULL,
    "name" varchar(255) NOT NULL,
    "age_min" integer DEFAULT 5,
    "age_max" integer DEFAULT 18,
    "staff_id" bigint,
    "max_athletes" integer DEFAULT 20,
    "start_time" time,
    "end_time" time,
    "training_days" jsonb,
    "is_active" boolean DEFAULT true,
    "is_archived" boolean DEFAULT false,
    "archived_at" timestamp with time zone,
    "archived_by" bigint,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "athlete_training_group" (
    "id" bigint NOT NULL,
    "athlete_id" bigint NOT NULL,
    "training_group_id" bigint NOT NULL,
    "joined_at" timestamp with time zone DEFAULT now(),
    "left_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "payment_method" (
    "id" bigint NOT NULL,
    "name" varchar(255) NOT NULL,
    "description" text,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "payment" (
    "id" bigint NOT NULL,
    "athlete_id" bigint NOT NULL,
    "amount" decimal(10,2) NOT NULL,
    "payment_method_id" bigint NOT NULL,
    "description" text,
    "is_paid" boolean DEFAULT false,
    "paid_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "document_type" (
    "id" bigint NOT NULL,
    "name" varchar(255) NOT NULL,
    "description" text,
    "allowed_formats" jsonb,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "document" (
    "id" bigint NOT NULL,
    "document_type_id" bigint NOT NULL,
    "file_path" varchar(255) NOT NULL,
    "file_name" varchar(255) NOT NULL,
    "file_size" bigint,
    "description" text,
    "is_private" boolean DEFAULT false,
    "is_archived" boolean DEFAULT false,
    "archived_at" timestamp with time zone,
    "archived_by" bigint,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "audit_record" (
    "id" bigint NOT NULL,
    "user_id" bigint NOT NULL,
    "action" varchar(255) NOT NULL,
    "table_name" varchar(255) NOT NULL,
    "record_id" bigint NOT NULL,
    "old_values" jsonb,
    "new_values" jsonb,
    "created_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "training_session" (
    "id" bigint NOT NULL,
    "training_group_id" bigint NOT NULL,
    "session_date" date NOT NULL,
    "start_time" time NOT NULL,
    "end_time" time NOT NULL,
    "notes" text,
    "is_closed" boolean DEFAULT false,
    "is_canceled" boolean DEFAULT false,
    "canceled_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "group_schedule" (
    "id" bigint NOT NULL,
    "training_group_id" bigint NOT NULL,
    "day_of_week" integer NOT NULL,
    "start_time" time NOT NULL,
    "end_time" time NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

CREATE TABLE "attendance_record" (
    "id" bigint NOT NULL,
    "training_session_id" bigint NOT NULL,
    "athlete_id" bigint NOT NULL,
    "attended" boolean DEFAULT false,
    "notes" text,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now()
);

-- Установка первичных ключей
ALTER TABLE "role" ADD CONSTRAINT "role_pkey" PRIMARY KEY ("id");
ALTER TABLE "permission" ADD CONSTRAINT "permission_pkey" PRIMARY KEY ("id");
ALTER TABLE "role_permission" ADD CONSTRAINT "role_permission_pkey" PRIMARY KEY ("id");
ALTER TABLE "auth_account" ADD CONSTRAINT "auth_account_pkey" PRIMARY KEY ("id");
ALTER TABLE "staff" ADD CONSTRAINT "staff_pkey" PRIMARY KEY ("id");
ALTER TABLE "parent" ADD CONSTRAINT "parent_pkey" PRIMARY KEY ("id");
ALTER TABLE "athlete" ADD CONSTRAINT "athlete_pkey" PRIMARY KEY ("id");
ALTER TABLE "training_group" ADD CONSTRAINT "training_group_pkey" PRIMARY KEY ("id");
ALTER TABLE "athlete_training_group" ADD CONSTRAINT "athlete_training_group_pkey" PRIMARY KEY ("id");
ALTER TABLE "payment_method" ADD CONSTRAINT "payment_method_pkey" PRIMARY KEY ("id");
ALTER TABLE "payment" ADD CONSTRAINT "payment_pkey" PRIMARY KEY ("id");
ALTER TABLE "document_type" ADD CONSTRAINT "document_type_pkey" PRIMARY KEY ("id");
ALTER TABLE "document" ADD CONSTRAINT "document_pkey" PRIMARY KEY ("id");
ALTER TABLE "audit_record" ADD CONSTRAINT "audit_record_pkey" PRIMARY KEY ("id");
ALTER TABLE "training_session" ADD CONSTRAINT "training_session_pkey" PRIMARY KEY ("id");
ALTER TABLE "group_schedule" ADD CONSTRAINT "group_schedule_pkey" PRIMARY KEY ("id");
ALTER TABLE "attendance_record" ADD CONSTRAINT "attendance_record_pkey" PRIMARY KEY ("id");

-- Установка уникальных ограничений
ALTER TABLE "auth_account" ADD CONSTRAINT "auth_account_phone_unique" UNIQUE ("phone");
ALTER TABLE "training_group" ADD CONSTRAINT "training_group_name_unique" UNIQUE ("name");

-- Установка внешних ключей
ALTER TABLE "role_permission" ADD CONSTRAINT "role_permission_role_id_foreign" FOREIGN KEY ("role_id") REFERENCES "role"("id");
ALTER TABLE "role_permission" ADD CONSTRAINT "role_permission_permission_id_foreign" FOREIGN KEY ("permission_id") REFERENCES "permission"("id");
ALTER TABLE "auth_account" ADD CONSTRAINT "auth_account_django_user_id_foreign" FOREIGN KEY ("django_user_id") REFERENCES "auth_user"("id");
ALTER TABLE "staff" ADD CONSTRAINT "staff_user_id_foreign" FOREIGN KEY ("user_id") REFERENCES "auth_account"("id");
ALTER TABLE "staff" ADD CONSTRAINT "staff_role_id_foreign" FOREIGN KEY ("role_id") REFERENCES "role"("id");
ALTER TABLE "parent" ADD CONSTRAINT "parent_user_id_foreign" FOREIGN KEY ("user_id") REFERENCES "auth_account"("id");
ALTER TABLE "athlete" ADD CONSTRAINT "athlete_user_id_foreign" FOREIGN KEY ("user_id") REFERENCES "auth_account"("id");
ALTER TABLE "training_group" ADD CONSTRAINT "training_group_staff_id_foreign" FOREIGN KEY ("staff_id") REFERENCES "staff"("id");
ALTER TABLE "athlete_training_group" ADD CONSTRAINT "athlete_training_group_athlete_id_foreign" FOREIGN KEY ("athlete_id") REFERENCES "athlete"("id");
ALTER TABLE "athlete_training_group" ADD CONSTRAINT "athlete_training_group_training_group_id_foreign" FOREIGN KEY ("training_group_id") REFERENCES "training_group"("id");
ALTER TABLE "payment" ADD CONSTRAINT "payment_athlete_id_foreign" FOREIGN KEY ("athlete_id") REFERENCES "athlete"("id");
ALTER TABLE "payment" ADD CONSTRAINT "payment_payment_method_id_foreign" FOREIGN KEY ("payment_method_id") REFERENCES "payment_method"("id");
ALTER TABLE "document" ADD CONSTRAINT "document_document_type_id_foreign" FOREIGN KEY ("document_type_id") REFERENCES "document_type"("id");
ALTER TABLE "audit_record" ADD CONSTRAINT "audit_record_user_id_foreign" FOREIGN KEY ("user_id") REFERENCES "auth_account"("id");
ALTER TABLE "training_session" ADD CONSTRAINT "training_session_training_group_id_foreign" FOREIGN KEY ("training_group_id") REFERENCES "training_group"("id");
ALTER TABLE "group_schedule" ADD CONSTRAINT "group_schedule_training_group_id_foreign" FOREIGN KEY ("training_group_id") REFERENCES "training_group"("id");
ALTER TABLE "attendance_record" ADD CONSTRAINT "attendance_record_training_session_id_foreign" FOREIGN KEY ("training_session_id") REFERENCES "training_session"("id");
ALTER TABLE "attendance_record" ADD CONSTRAINT "attendance_record_athlete_id_foreign" FOREIGN KEY ("athlete_id") REFERENCES "athlete"("id");

-- Создание индексов
CREATE INDEX "role_permission_role_id_index" ON "role_permission" ("role_id");
CREATE INDEX "role_permission_permission_id_index" ON "role_permission" ("permission_id");
CREATE INDEX "auth_account_phone_index" ON "auth_account" ("phone");
CREATE INDEX "auth_account_django_user_id_index" ON "auth_account" ("django_user_id");
CREATE INDEX "staff_user_id_index" ON "staff" ("user_id");
CREATE INDEX "staff_role_id_index" ON "staff" ("role_id");
CREATE INDEX "parent_user_id_index" ON "parent" ("user_id");
CREATE INDEX "athlete_user_id_index" ON "athlete" ("user_id");
CREATE INDEX "training_group_staff_id_index" ON "training_group" ("staff_id");
CREATE INDEX "athlete_training_group_athlete_id_index" ON "athlete_training_group" ("athlete_id");
CREATE INDEX "athlete_training_group_training_group_id_index" ON "athlete_training_group" ("training_group_id");
CREATE INDEX "payment_athlete_id_index" ON "payment" ("athlete_id");
CREATE INDEX "payment_payment_method_id_index" ON "payment" ("payment_method_id");
CREATE INDEX "document_document_type_id_index" ON "document" ("document_type_id");
CREATE INDEX "audit_record_user_id_index" ON "audit_record" ("user_id");
CREATE INDEX "training_session_training_group_id_index" ON "training_session" ("training_group_id");
CREATE INDEX "group_schedule_training_group_id_index" ON "group_schedule" ("training_group_id");
CREATE INDEX "attendance_record_training_session_id_index" ON "attendance_record" ("training_session_id");
CREATE INDEX "attendance_record_athlete_id_index" ON "attendance_record" ("athlete_id");

-- Вставка базовых данных
INSERT INTO "role" ("id", "name", "description") VALUES 
(1, 'Администратор', 'Полный доступ к системе'),
(2, 'Тренер', 'Управление группами и тренировками'),
(3, 'Родитель', 'Просмотр информации о ребенке'),
(4, 'Спортсмен', 'Просмотр своих данных');

INSERT INTO "permission" ("id", "name", "code_name", "description") VALUES 
(1, 'Просмотр пользователей', 'view_users', 'Просмотр списка пользователей'),
(2, 'Создание пользователей', 'create_users', 'Создание новых пользователей'),
(3, 'Редактирование пользователей', 'edit_users', 'Редактирование данных пользователей'),
(4, 'Удаление пользователей', 'delete_users', 'Удаление пользователей'),
(5, 'Просмотр групп', 'view_groups', 'Просмотр тренировочных групп'),
(6, 'Создание групп', 'create_groups', 'Создание новых групп'),
(7, 'Редактирование групп', 'edit_groups', 'Редактирование групп'),
(8, 'Удаление групп', 'delete_groups', 'Удаление групп');

INSERT INTO "payment_method" ("id", "name", "description") VALUES 
(1, 'Наличные', 'Оплата наличными'),
(2, 'Банковская карта', 'Оплата банковской картой'),
(3, 'Безналичный расчет', 'Безналичный расчет');

INSERT INTO "document_type" ("id", "name", "description", "allowed_formats") VALUES 
(1, 'Медицинская справка', 'Медицинская справка о состоянии здоровья', '["pdf", "jpg", "png"]'),
(2, 'Согласие родителей', 'Согласие родителей на занятия спортом', '["pdf", "doc", "docx"]'),
(3, 'Фотография', 'Фотография спортсмена', '["jpg", "png", "jpeg"]');

-- Настройка автоинкремента для ID
CREATE SEQUENCE role_id_seq START WITH 5;
CREATE SEQUENCE permission_id_seq START WITH 9;
CREATE SEQUENCE auth_account_id_seq START WITH 1;
CREATE SEQUENCE staff_id_seq START WITH 1;
CREATE SEQUENCE parent_id_seq START WITH 1;
CREATE SEQUENCE athlete_id_seq START WITH 1;
CREATE SEQUENCE training_group_id_seq START WITH 1;
CREATE SEQUENCE athlete_training_group_id_seq START WITH 1;
CREATE SEQUENCE payment_method_id_seq START WITH 4;
CREATE SEQUENCE payment_id_seq START WITH 1;
CREATE SEQUENCE document_type_id_seq START WITH 4;
CREATE SEQUENCE document_id_seq START WITH 1;
CREATE SEQUENCE audit_record_id_seq START WITH 1;
CREATE SEQUENCE training_session_id_seq START WITH 1;
CREATE SEQUENCE group_schedule_id_seq START WITH 1;
CREATE SEQUENCE attendance_record_id_seq START WITH 1;

ALTER TABLE "role" ALTER COLUMN "id" SET DEFAULT nextval('role_id_seq');
ALTER TABLE "permission" ALTER COLUMN "id" SET DEFAULT nextval('permission_id_seq');
ALTER TABLE "auth_account" ALTER COLUMN "id" SET DEFAULT nextval('auth_account_id_seq');
ALTER TABLE "staff" ALTER COLUMN "id" SET DEFAULT nextval('staff_id_seq');
ALTER TABLE "parent" ALTER COLUMN "id" SET DEFAULT nextval('parent_id_seq');
ALTER TABLE "athlete" ALTER COLUMN "id" SET DEFAULT nextval('athlete_id_seq');
ALTER TABLE "training_group" ALTER COLUMN "id" SET DEFAULT nextval('training_group_id_seq');
ALTER TABLE "athlete_training_group" ALTER COLUMN "id" SET DEFAULT nextval('athlete_training_group_id_seq');
ALTER TABLE "payment_method" ALTER COLUMN "id" SET DEFAULT nextval('payment_method_id_seq');
ALTER TABLE "payment" ALTER COLUMN "id" SET DEFAULT nextval('payment_id_seq');
ALTER TABLE "document_type" ALTER COLUMN "id" SET DEFAULT nextval('document_type_id_seq');
ALTER TABLE "document" ALTER COLUMN "id" SET DEFAULT nextval('document_id_seq');
ALTER TABLE "audit_record" ALTER COLUMN "id" SET DEFAULT nextval('audit_record_id_seq');
ALTER TABLE "training_session" ALTER COLUMN "id" SET DEFAULT nextval('training_session_id_seq');
ALTER TABLE "group_schedule" ALTER COLUMN "id" SET DEFAULT nextval('group_schedule_id_seq');
ALTER TABLE "attendance_record" ALTER COLUMN "id" SET DEFAULT nextval('attendance_record_id_seq'); 
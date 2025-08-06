CREATE TABLE "payment_method"(
    "id" INTEGER NOT NULL DEFAULT 'nextval(' payment_method_id_seq ')',
    "name" VARCHAR(255) NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT 'DEFAULT TRUE'
);
ALTER TABLE
    "payment_method" ADD PRIMARY KEY("id");
ALTER TABLE
    "payment_method" ADD CONSTRAINT "payment_method_name_unique" UNIQUE("name");
CREATE TABLE "payment"(
    "id" INTEGER NOT NULL DEFAULT 'nextval(' payment_id_seq ')',
    "athlete_id" BIGINT NOT NULL,
    "training_group_id" BIGINT NOT NULL,
    "payer_id" BIGINT NOT NULL,
    "amount" DECIMAL(8, 2) NOT NULL,
    "payment_method_id" BIGINT NOT NULL,
    "comment" TEXT NOT NULL,
    "billing_period_start" DATE NOT NULL,
    "billing_period_end" DATE NOT NULL,
    "is_archived" BOOLEAN NOT NULL DEFAULT 'DEFAULT FALSE',
    "paid_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL DEFAULT CURRENT_TIMESTAMP,
    "is_automated" BOOLEAN NOT NULL,
    "is_paid" BOOLEAN NOT NULL DEFAULT 'DEFAULT FALSE',
    "invoice_number" VARCHAR(255) NOT NULL,
    "created_by" BIGINT NOT NULL,
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL
);
ALTER TABLE
    "payment" ADD PRIMARY KEY("id");
CREATE INDEX "payment_athlete_id_index" ON
    "payment"("athlete_id");
CREATE INDEX "payment_payment_method_id_index" ON
    "payment"("payment_method_id");
ALTER TABLE
    "payment" ADD CONSTRAINT "payment_invoice_number_unique" UNIQUE("invoice_number");
CREATE TABLE "audit_record"(
    "id" INTEGER NOT NULL DEFAULT 'nextval(' audit_record_id_seq ')',
    "user_id" BIGINT NOT NULL,
    "action" VARCHAR(255) NOT NULL,
    "content_type_id" BIGINT NOT NULL,
    "object_id" BIGINT NOT NULL,
    "timestamp" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "details" TEXT NOT NULL
);
ALTER TABLE
    "audit_record" ADD PRIMARY KEY("id");
CREATE INDEX "audit_record_user_id_index" ON
    "audit_record"("user_id");
CREATE TABLE "auth_group"(
    "id" INTEGER NOT NULL,
    "name" VARCHAR(255) NOT NULL
);
ALTER TABLE
    "auth_group" ADD PRIMARY KEY("id");
ALTER TABLE
    "auth_group" ADD CONSTRAINT "auth_group_name_unique" UNIQUE("name");
CREATE TABLE "auth_group_permissions"(
    "id" INTEGER NOT NULL,
    "group_id" INTEGER NOT NULL,
    "permission_id" INTEGER NOT NULL
);
ALTER TABLE
    "auth_group_permissions" ADD PRIMARY KEY("id");
CREATE TABLE "auth_permission"(
    "id" INTEGER NOT NULL,
    "content_type_id" INTEGER NOT NULL,
    "codename" VARCHAR(255) NOT NULL,
    "name" VARCHAR(255) NOT NULL
);
ALTER TABLE
    "auth_permission" ADD PRIMARY KEY("id");
CREATE TABLE "auth_user"(
    "id" INTEGER NOT NULL,
    "username" VARCHAR(255) NOT NULL,
    "password" VARCHAR(255) NOT NULL,
    "last_name" VARCHAR(255) NOT NULL,
    "first_name" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) NOT NULL,
    "is_superuser" BOOLEAN NOT NULL,
    "is_staff" BOOLEAN NOT NULL,
    "is_active" BOOLEAN NOT NULL,
    "last_login" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "date_joined" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);
ALTER TABLE
    "auth_user" ADD PRIMARY KEY("id");
CREATE TABLE "auth_user_groups"(
    "id" INTEGER NOT NULL,
    "user_id" INTEGER NOT NULL,
    "group_id" INTEGER NOT NULL
);
CREATE INDEX "auth_user_groups_user_id_group_id_index" ON
    "auth_user_groups"("user_id", "group_id");
ALTER TABLE
    "auth_user_groups" ADD PRIMARY KEY("id");
CREATE TABLE "auth_user_user_permissions"(
    "id" INTEGER NOT NULL,
    "user_id" INTEGER NOT NULL,
    "permission_id" INTEGER NOT NULL
);
ALTER TABLE
    "auth_user_user_permissions" ADD PRIMARY KEY("id");
CREATE TABLE "django_admin_log"(
    "id" INTEGER NOT NULL,
    "object_id" TEXT NULL,
    "object_repr" VARCHAR(255) NOT NULL,
    "action_flag" TEXT NOT NULL,
    "change_message" TEXT NOT NULL,
    "content_type_id" INTEGER NULL,
    "user_id" INTEGER NOT NULL,
    "action_time" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);
ALTER TABLE
    "django_admin_log" ADD PRIMARY KEY("id");
CREATE TABLE "django_content_type"(
    "id" INTEGER NOT NULL,
    "app_label" VARCHAR(255) NOT NULL,
    "model" VARCHAR(255) NOT NULL
);
ALTER TABLE
    "django_content_type" ADD PRIMARY KEY("id");
CREATE TABLE "django_migrations"(
    "id" INTEGER NOT NULL,
    "app" VARCHAR(255) NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "applied" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);
ALTER TABLE
    "django_migrations" ADD PRIMARY KEY("id");
CREATE TABLE "django_session"(
    "session_key" VARCHAR(255) NOT NULL,
    "session_data" TEXT NOT NULL,
    "expire_date" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL
);
ALTER TABLE
    "django_session" ADD PRIMARY KEY("session_key");
CREATE TABLE "staff"(
    "id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "description" TEXT NOT NULL,
    "photo" TEXT NOT NULL,
    "is_archived" BOOLEAN NOT NULL DEFAULT 'DEFAULT FALSE',
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL,
    "phone" VARCHAR(255) NOT NULL,
    "birth_date" DATE NOT NULL
);
ALTER TABLE
    "staff" ADD PRIMARY KEY("id");
ALTER TABLE
    "staff" ADD CONSTRAINT "staff_user_id_unique" UNIQUE("user_id");
ALTER TABLE
    "staff" ADD CONSTRAINT "staff_phone_unique" UNIQUE("phone");
CREATE TABLE "parent"(
    "id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "photo" TEXT NOT NULL,
    "is_archived" BOOLEAN NOT NULL DEFAULT 'DEFAULT FALSE',
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL
);
ALTER TABLE
    "parent" ADD PRIMARY KEY("id");
ALTER TABLE
    "parent" ADD CONSTRAINT "parent_user_id_unique" UNIQUE("user_id");
CREATE TABLE "athlete"(
    "id" BIGINT NOT NULL,
    "user_id" BIGINT NOT NULL,
    "birth_date" DATE NOT NULL,
    "photo" TEXT NOT NULL,
    "is_archived" BOOLEAN NOT NULL DEFAULT 'DEFAULT FALSE',
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL
);
ALTER TABLE
    "athlete" ADD PRIMARY KEY("id");
ALTER TABLE
    "athlete" ADD CONSTRAINT "athlete_user_id_unique" UNIQUE("user_id");
CREATE TABLE "training_group"(
    "id" BIGINT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "age_min" INTEGER NOT NULL,
    "age_max" INTEGER NOT NULL DEFAULT '18',
    "staff_id" BIGINT NULL,
    "max_athletes" INTEGER NOT NULL DEFAULT '20',
    "is_active" BOOLEAN NOT NULL DEFAULT 'DEFAULT TRUE',
    "is_archived" BOOLEAN NOT NULL DEFAULT 'DEFAULT FALSE',
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL
);
ALTER TABLE
    "training_group" ADD PRIMARY KEY("id");
ALTER TABLE
    "training_group" ADD CONSTRAINT "training_group_name_unique" UNIQUE("name");
CREATE TABLE "athlete_training_group"(
    "id" BIGINT NOT NULL,
    "athlete_id" BIGINT NOT NULL,
    "training_group_id" BIGINT NOT NULL
);
ALTER TABLE
    "athlete_training_group" ADD CONSTRAINT "athlete_training_group_athlete_id_training_group_id_unique" UNIQUE("athlete_id", "training_group_id");
ALTER TABLE
    "athlete_training_group" ADD PRIMARY KEY("id");
CREATE TABLE "athlete_parent"(
    "id" BIGINT NOT NULL,
    "athlete_id" BIGINT NOT NULL,
    "parent_id" BIGINT NOT NULL
);
ALTER TABLE
    "athlete_parent" ADD CONSTRAINT "athlete_parent_athlete_id_parent_id_unique" UNIQUE("athlete_id", "parent_id");
ALTER TABLE
    "athlete_parent" ADD PRIMARY KEY("id");
CREATE TABLE "group_schedule"(
    "id" INTEGER NOT NULL DEFAULT 'nextval(' group_schedule_id_seq ')',
    "training_group_id" BIGINT NOT NULL,
    "weekday" INTEGER NOT NULL,
    "start_time" TIME(0) WITHOUT TIME ZONE NOT NULL,
    "end_time" TIME(0) WITHOUT TIME ZONE NOT NULL
);
ALTER TABLE
    "group_schedule" ADD CONSTRAINT "group_schedule_training_group_id_weekday_start_time_unique" UNIQUE(
        "training_group_id",
        "weekday",
        "start_time"
    );
ALTER TABLE
    "group_schedule" ADD PRIMARY KEY("id");
CREATE INDEX "group_schedule_training_group_id_index" ON
    "group_schedule"("training_group_id");
CREATE TABLE "training_session"(
    "id" INTEGER NOT NULL DEFAULT 'nextval(' training_session_id_seq ')',
    "training_group_id" BIGINT NOT NULL,
    "date" DATE NOT NULL,
    "start_time" TIME(0) WITHOUT TIME ZONE NOT NULL,
    "end_time" TIME(0) WITHOUT TIME ZONE NOT NULL,
    "is_closed" BOOLEAN NOT NULL DEFAULT 'DEFAULT FALSE',
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_canceled" BOOLEAN NOT NULL DEFAULT 'DEFAULT FALSE',
    "canceled_by" BIGINT NULL,
    "canceled_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL
);
ALTER TABLE
    "training_session" ADD PRIMARY KEY("id");
CREATE INDEX "training_session_training_group_id_index" ON
    "training_session"("training_group_id");
CREATE TABLE "attendance_record"(
    "id" INTEGER NOT NULL DEFAULT 'nextval(' attendance_record_id_seq ')',
    "athlete_id" BIGINT NOT NULL,
    "session_id" BIGINT NOT NULL,
    "was_present" BOOLEAN NOT NULL,
    "marked_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "marked_by" BIGINT NOT NULL
);
ALTER TABLE
    "attendance_record" ADD CONSTRAINT "attendance_record_athlete_id_session_id_unique" UNIQUE("athlete_id", "session_id");
ALTER TABLE
    "attendance_record" ADD PRIMARY KEY("id");
CREATE INDEX "attendance_record_athlete_id_index" ON
    "attendance_record"("athlete_id");
CREATE TABLE "document_type"(
    "id" INTEGER NOT NULL DEFAULT 'nextval(' document_type_id_seq ')',
    "name" VARCHAR(255) NOT NULL
);
ALTER TABLE
    "document_type" ADD PRIMARY KEY("id");
ALTER TABLE
    "document_type" ADD CONSTRAINT "document_type_name_unique" UNIQUE("name");
CREATE TABLE "document"(
    "id" INTEGER NOT NULL DEFAULT 'nextval(' document_id_seq ')',
    "file" VARCHAR(255) NOT NULL,
    "file_type" VARCHAR(255) NOT NULL,
    "file_size" INTEGER NOT NULL,
    "document_type_id" BIGINT NOT NULL,
    "content_type_id" BIGINT NOT NULL,
    "object_id" BIGINT NOT NULL,
    "uploaded_by" BIGINT NULL,
    "uploaded_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_private" BOOLEAN NOT NULL DEFAULT 'DEFAULT FALSE',
    "comment" TEXT NOT NULL,
    "is_archived" BOOLEAN NOT NULL DEFAULT 'DEFAULT FALSE',
    "archived_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "archived_by" BIGINT NULL
);
CREATE INDEX "document_content_type_id_object_id_index" ON
    "document"("content_type_id", "object_id");
ALTER TABLE
    "document" ADD PRIMARY KEY("id");
CREATE INDEX "document_document_type_id_index" ON
    "document"("document_type_id");
CREATE INDEX "document_content_type_id_index" ON
    "document"("content_type_id");
ALTER TABLE
    "parent" ADD CONSTRAINT "parent_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "auth_user"("id");
ALTER TABLE
    "document" ADD CONSTRAINT "document_document_type_id_foreign" FOREIGN KEY("document_type_id") REFERENCES "document_type"("id");
ALTER TABLE
    "attendance_record" ADD CONSTRAINT "attendance_record_marked_by_foreign" FOREIGN KEY("marked_by") REFERENCES "staff"("id");
ALTER TABLE
    "audit_record" ADD CONSTRAINT "audit_record_content_type_id_foreign" FOREIGN KEY("content_type_id") REFERENCES "django_content_type"("id");
ALTER TABLE
    "training_group" ADD CONSTRAINT "training_group_staff_id_foreign" FOREIGN KEY("staff_id") REFERENCES "staff"("id");
ALTER TABLE
    "parent" ADD CONSTRAINT "parent_archived_by_foreign" FOREIGN KEY("archived_by") REFERENCES "staff"("id");
ALTER TABLE
    "attendance_record" ADD CONSTRAINT "attendance_record_athlete_id_foreign" FOREIGN KEY("athlete_id") REFERENCES "athlete"("id");
ALTER TABLE
    "athlete_parent" ADD CONSTRAINT "athlete_parent_athlete_id_foreign" FOREIGN KEY("athlete_id") REFERENCES "athlete"("id");
ALTER TABLE
    "payment" ADD CONSTRAINT "payment_payment_method_id_foreign" FOREIGN KEY("payment_method_id") REFERENCES "payment_method"("id");
ALTER TABLE
    "training_group" ADD CONSTRAINT "training_group_archived_by_foreign" FOREIGN KEY("archived_by") REFERENCES "staff"("id");
ALTER TABLE
    "athlete_training_group" ADD CONSTRAINT "athlete_training_group_athlete_id_foreign" FOREIGN KEY("athlete_id") REFERENCES "athlete"("id");
ALTER TABLE
    "payment" ADD CONSTRAINT "payment_archived_by_foreign" FOREIGN KEY("archived_by") REFERENCES "staff"("id");
ALTER TABLE
    "payment" ADD CONSTRAINT "payment_training_group_id_foreign" FOREIGN KEY("training_group_id") REFERENCES "training_group"("id");
ALTER TABLE
    "auth_user_user_permissions" ADD CONSTRAINT "auth_user_user_permissions_permission_id_foreign" FOREIGN KEY("permission_id") REFERENCES "auth_permission"("id");
ALTER TABLE
    "django_admin_log" ADD CONSTRAINT "django_admin_log_content_type_id_foreign" FOREIGN KEY("content_type_id") REFERENCES "django_content_type"("id");
ALTER TABLE
    "training_session" ADD CONSTRAINT "training_session_training_group_id_foreign" FOREIGN KEY("training_group_id") REFERENCES "training_group"("id");
ALTER TABLE
    "athlete" ADD CONSTRAINT "athlete_archived_by_foreign" FOREIGN KEY("archived_by") REFERENCES "staff"("id");
ALTER TABLE
    "audit_record" ADD CONSTRAINT "audit_record_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "auth_user"("id");
ALTER TABLE
    "staff" ADD CONSTRAINT "staff_archived_by_foreign" FOREIGN KEY("archived_by") REFERENCES "auth_user"("id");
ALTER TABLE
    "django_admin_log" ADD CONSTRAINT "django_admin_log_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "auth_user"("id");
ALTER TABLE
    "document" ADD CONSTRAINT "document_uploaded_by_foreign" FOREIGN KEY("uploaded_by") REFERENCES "auth_user"("id");
ALTER TABLE
    "auth_group_permissions" ADD CONSTRAINT "auth_group_permissions_permission_id_foreign" FOREIGN KEY("permission_id") REFERENCES "auth_permission"("id");
ALTER TABLE
    "attendance_record" ADD CONSTRAINT "attendance_record_session_id_foreign" FOREIGN KEY("session_id") REFERENCES "training_session"("id");
ALTER TABLE
    "payment" ADD CONSTRAINT "payment_payer_id_foreign" FOREIGN KEY("payer_id") REFERENCES "auth_user"("id");
ALTER TABLE
    "document" ADD CONSTRAINT "document_archived_by_foreign" FOREIGN KEY("archived_by") REFERENCES "staff"("id");
ALTER TABLE
    "athlete" ADD CONSTRAINT "athlete_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "auth_user"("id");
ALTER TABLE
    "document" ADD CONSTRAINT "document_content_type_id_foreign" FOREIGN KEY("content_type_id") REFERENCES "django_content_type"("id");
ALTER TABLE
    "auth_group_permissions" ADD CONSTRAINT "auth_group_permissions_group_id_foreign" FOREIGN KEY("group_id") REFERENCES "auth_group"("id");
ALTER TABLE
    "auth_permission" ADD CONSTRAINT "auth_permission_content_type_id_foreign" FOREIGN KEY("content_type_id") REFERENCES "django_content_type"("id");
ALTER TABLE
    "staff" ADD CONSTRAINT "staff_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "auth_user"("id");
ALTER TABLE
    "group_schedule" ADD CONSTRAINT "group_schedule_training_group_id_foreign" FOREIGN KEY("training_group_id") REFERENCES "training_group"("id");
ALTER TABLE
    "payment" ADD CONSTRAINT "payment_created_by_foreign" FOREIGN KEY("created_by") REFERENCES "staff"("id");
ALTER TABLE
    "training_session" ADD CONSTRAINT "training_session_canceled_by_foreign" FOREIGN KEY("canceled_by") REFERENCES "staff"("id");
ALTER TABLE
    "auth_user_user_permissions" ADD CONSTRAINT "auth_user_user_permissions_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "auth_user"("id");
ALTER TABLE
    "auth_user_groups" ADD CONSTRAINT "auth_user_groups_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "auth_user"("id");
ALTER TABLE
    "athlete_parent" ADD CONSTRAINT "athlete_parent_parent_id_foreign" FOREIGN KEY("parent_id") REFERENCES "parent"("id");
ALTER TABLE
    "athlete_training_group" ADD CONSTRAINT "athlete_training_group_training_group_id_foreign" FOREIGN KEY("training_group_id") REFERENCES "training_group"("id");
ALTER TABLE
    "auth_user_groups" ADD CONSTRAINT "auth_user_groups_group_id_foreign" FOREIGN KEY("group_id") REFERENCES "auth_group"("id");
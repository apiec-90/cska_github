from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    PaymentMethod, Staff, Parent, Athlete, TrainingGroup, 
    AthleteTrainingGroup, AthleteParent, GroupSchedule, 
    TrainingSession, AttendanceRecord, DocumentType, 
    Document, Payment, AuditRecord
)

# Регистрируем стандартные Django модели
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'birth_date', 'is_archived')
    list_filter = ('is_archived', 'birth_date')
    search_fields = ('user__first_name', 'user__last_name', 'phone')
    ordering = ('user__last_name', 'user__first_name')
    raw_id_fields = ('user', 'archived_by')

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_archived')
    list_filter = ('is_archived',)
    search_fields = ('user__first_name', 'user__last_name')
    ordering = ('user__last_name', 'user__first_name')
    raw_id_fields = ('user', 'archived_by')

@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'is_archived')
    list_filter = ('is_archived', 'birth_date')
    search_fields = ('user__first_name', 'user__last_name')
    ordering = ('user__last_name', 'user__first_name')
    raw_id_fields = ('user', 'archived_by')

@admin.register(TrainingGroup)
class TrainingGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'age_min', 'age_max', 'staff', 'max_athletes', 'is_active', 'is_archived')
    list_filter = ('is_active', 'is_archived', 'age_min', 'age_max')
    search_fields = ('name',)
    ordering = ('name',)
    raw_id_fields = ('staff', 'archived_by')

@admin.register(AthleteTrainingGroup)
class AthleteTrainingGroupAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'training_group')
    list_filter = ('training_group',)
    search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'training_group__name')
    ordering = ('athlete__user__last_name', 'training_group__name')
    raw_id_fields = ('athlete', 'training_group')

@admin.register(AthleteParent)
class AthleteParentAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'parent')
    list_filter = ('parent',)
    search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'parent__user__first_name', 'parent__user__last_name')
    ordering = ('athlete__user__last_name', 'parent__user__last_name')
    raw_id_fields = ('athlete', 'parent')

@admin.register(GroupSchedule)
class GroupScheduleAdmin(admin.ModelAdmin):
    list_display = ('training_group', 'weekday', 'start_time', 'end_time')
    list_filter = ('training_group', 'weekday')
    search_fields = ('training_group__name',)
    ordering = ('training_group__name', 'weekday', 'start_time')
    raw_id_fields = ('training_group',)

@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('training_group', 'date', 'start_time', 'end_time', 'is_closed', 'is_canceled')
    list_filter = ('training_group', 'date', 'is_closed', 'is_canceled')
    search_fields = ('training_group__name',)
    ordering = ('-date', 'training_group__name')
    raw_id_fields = ('training_group', 'canceled_by')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'session', 'was_present', 'marked_at', 'marked_by')
    list_filter = ('was_present', 'marked_at', 'session__training_group')
    search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'session__training_group__name')
    ordering = ('-marked_at', 'athlete__user__last_name')
    raw_id_fields = ('athlete', 'session', 'marked_by')

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('document_type', 'content_type', 'object_id', 'uploaded_by', 'uploaded_at', 'is_private', 'is_archived')
    list_filter = ('document_type', 'content_type', 'is_private', 'is_archived', 'uploaded_at')
    search_fields = ('document_type__name', 'comment')
    ordering = ('-uploaded_at',)
    raw_id_fields = ('document_type', 'content_type', 'uploaded_by', 'archived_by')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'training_group', 'payer', 'amount', 'payment_method', 'is_paid', 'is_archived')
    list_filter = ('payment_method', 'is_paid', 'is_archived', 'is_automated', 'billing_period_start', 'billing_period_end')
    search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'payer__first_name', 'payer__last_name', 'invoice_number')
    ordering = ('-paid_at', 'athlete__user__last_name')
    raw_id_fields = ('athlete', 'training_group', 'payer', 'payment_method', 'created_by', 'archived_by')

@admin.register(AuditRecord)
class AuditRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'content_type', 'object_id', 'timestamp')
    list_filter = ('action', 'content_type', 'timestamp')
    search_fields = ('user__first_name', 'user__last_name', 'action', 'details')
    ordering = ('-timestamp',)
    raw_id_fields = ('user', 'content_type')
    readonly_fields = ('timestamp',)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    PaymentMethod, Staff, Parent, Athlete, Trainer, TrainingGroup, 
    AthleteTrainingGroup, AthleteParent, GroupSchedule, 
    TrainingSession, AttendanceRecord, DocumentType, 
    Document, Payment, AuditRecord
)

# Регистрируем стандартные Django модели
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Inline для связей спортсмен-родитель
class AthleteParentInline(admin.TabularInline):
    model = AthleteParent
    extra = 1

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'experience_years', 'get_groups_count', 'get_athletes_count', 'is_archived']
    list_filter = ['specialization', 'is_archived', 'experience_years']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'specialization']
    
    def get_groups_count(self, obj):
        return obj.get_groups_count()
    get_groups_count.short_description = 'Групп'
    
    def get_athletes_count(self, obj):
        return obj.get_athletes_count()
    get_athletes_count.short_description = 'Спортсменов'

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_role_display', 'phone', 'birth_date', 'is_archived']
    list_filter = ['role', 'is_archived']
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    
    def get_role_display(self, obj):
        return obj.get_role_display()
    get_role_display.short_description = 'Роль'

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_archived')
    list_filter = ('is_archived',)
    search_fields = ('user__first_name', 'user__last_name')
    ordering = ('user__last_name', 'user__first_name')

@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'get_parents_display', 'is_archived')
    list_filter = ('is_archived', 'birth_date')
    search_fields = ('user__first_name', 'user__last_name')
    ordering = ('user__last_name', 'user__first_name')
    inlines = [AthleteParentInline]
    
    def get_parents_display(self, obj):
        """Отображение родителей в списке"""
        parents = obj.get_parents()
        if parents:
            return ", ".join([f"{parent.parent.user.first_name} {parent.parent.user.last_name}" for parent in parents])
        return "Не указаны"
    get_parents_display.short_description = "Родители"

@admin.register(TrainingGroup)
class TrainingGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'age_min', 'age_max', 'trainer', 'get_athletes_count', 'get_parents_count', 'is_active', 'is_archived')
    list_filter = ('is_active', 'is_archived', 'age_min', 'age_max')
    search_fields = ('name', 'trainer__user__first_name', 'trainer__user__last_name')
    ordering = ('name',)

@admin.register(AthleteTrainingGroup)
class AthleteTrainingGroupAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'training_group')
    list_filter = ('training_group',)
    search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'training_group__name')
    ordering = ('athlete__user__last_name', 'training_group__name')

@admin.register(AthleteParent)
class AthleteParentAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'parent')
    list_filter = ('parent',)
    search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'parent__user__first_name', 'parent__user__last_name')
    ordering = ('athlete__user__last_name', 'parent__user__last_name')

@admin.register(GroupSchedule)
class GroupScheduleAdmin(admin.ModelAdmin):
    list_display = ('training_group', 'weekday', 'start_time', 'end_time')
    list_filter = ('training_group', 'weekday')
    search_fields = ('training_group__name',)
    ordering = ('training_group__name', 'weekday', 'start_time')

@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('training_group', 'date', 'start_time', 'end_time', 'is_closed', 'is_canceled')
    list_filter = ('training_group', 'date', 'is_closed', 'is_canceled')
    search_fields = ('training_group__name',)
    ordering = ('-date', 'training_group__name')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'session', 'was_present', 'marked_at', 'marked_by')
    list_filter = ('was_present', 'marked_at', 'session__training_group')
    search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'session__training_group__name')
    ordering = ('-marked_at', 'athlete__user__last_name')

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

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('athlete', 'training_group', 'payer', 'amount', 'payment_method', 'is_paid', 'is_archived')
    list_filter = ('payment_method', 'is_paid', 'is_archived', 'is_automated', 'billing_period_start', 'billing_period_end')
    search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'payer__first_name', 'payer__last_name', 'invoice_number')
    ordering = ('-paid_at', 'athlete__user__last_name')

@admin.register(AuditRecord)
class AuditRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'content_type', 'object_id', 'timestamp')
    list_filter = ('action', 'content_type', 'timestamp')
    search_fields = ('user__first_name', 'user__last_name', 'action', 'details')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

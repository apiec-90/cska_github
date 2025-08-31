"""
Остальные админки: Payment, Document, AuditRecord и т.д.
"""
from django.contrib import admin

from core.models import (
    PaymentMethod, DocumentType, Document, 
    Payment, AuditRecord, RegistrationDraft
)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Админка способов оплаты"""
    
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['name']


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    """Админка типов документов"""
    
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Админка документов"""
    
    list_display = [
        'document_type', 'content_type', 'object_id', 
        'uploaded_by', 'uploaded_at', 'is_private', 'is_archived'
    ]
    list_filter = [
        'document_type', 'content_type', 'is_private', 
        'is_archived', 'uploaded_at'
    ]
    search_fields = ['document_type__name', 'comment']
    ordering = ['-uploaded_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Админка платежей"""
    
    list_display = [
        'athlete', 'training_group', 'payer', 'amount', 
        'payment_method', 'is_paid', 'is_archived'
    ]
    list_filter = [
        'payment_method', 'is_paid', 'is_archived', 
        'is_automated', 'billing_period_start', 'billing_period_end'
    ]
    search_fields = [
        'athlete__user__first_name', 'athlete__user__last_name', 
        'payer__first_name', 'payer__last_name', 'invoice_number'
    ]
    ordering = ['-paid_at', 'athlete__user__last_name']


@admin.register(AuditRecord)
class AuditRecordAdmin(admin.ModelAdmin):
    """Админка записей аудита"""
    
    list_display = ['user', 'action', 'content_type', 'object_id', 'timestamp']
    list_filter = ['action', 'content_type', 'timestamp']
    search_fields = ['user__first_name', 'user__last_name', 'action', 'details']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']


@admin.register(RegistrationDraft)
class RegistrationDraftAdmin(admin.ModelAdmin):
    """Админка черновиков регистрации"""
    
    list_display = [
        'user', 'created_by', 'role', 'staff_role', 
        'current_step', 'is_completed', 'created_at'
    ]
    list_filter = ['role', 'is_completed', 'current_step', 'created_at']
    search_fields = [
        'user__username', 'user__email', 
        'created_by__username'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
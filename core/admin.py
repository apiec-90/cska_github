from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.admin.utils import unquote
from django.utils.html import format_html
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType

from .models import (
    PaymentMethod, Staff, Parent, Athlete, Trainer, TrainingGroup, 
    AthleteTrainingGroup, AthleteParent, GroupSchedule, 
    TrainingSession, AttendanceRecord, DocumentType, 
    Document, Payment, AuditRecord, RegistrationDraft
)
from .forms import Step1UserForm, Step2RoleForm, TrainerForm, ParentForm, AthleteForm

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

class RegistrationAdminView(View):
    """Базовый класс для admin views регистрации"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class Step1RegistrationView(RegistrationAdminView):
    """Шаг 1: Создание временного пользователя"""
    
    def get(self, request):
        # Очистка существующего черновика
        draft_id = request.session.get('draft_id')
        if draft_id:
            try:
                draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
                draft.safe_dispose()
                print(f"Cleaned up existing draft #{draft_id}")
            except RegistrationDraft.DoesNotExist:
                pass
            request.session.pop('draft_id', None)
        
        form = Step1UserForm()
        return render(request, 'admin/core/registration/step1.html', {
            'form': form,
            'title': 'Шаг 1 - Создание пользователя',
            'opts': User._meta,
        })
    
    def post(self, request):
        form = Step1UserForm(request.POST)
        if form.is_valid():
            # Создаем временного пользователя
            user = form.save(commit=False)
            user.is_active = False  # Временно неактивен
            user.save()
            
            # Создаем черновик регистрации
            draft = RegistrationDraft.objects.create(
                user=user,
                created_by=request.user,
                current_step=1
            )
            
            request.session['draft_id'] = draft.id
            print(f"Created draft #{draft.id} for user {user.username}")
            messages.success(request, f'Пользователь {user.username} создан. Переходим к выбору роли.')
            
            return HttpResponseRedirect(reverse('admin:register_step2', args=[draft.id]))
        
        return render(request, 'admin/core/registration/step1.html', {
            'form': form,
            'title': 'Шаг 1 - Создание пользователя',
            'opts': User._meta,
        })

class Step2RegistrationView(RegistrationAdminView):
    """Шаг 2: Выбор роли"""
    
    def get(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или уже завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))
        
        form = Step2RoleForm(initial={'role': draft.role})
        
        return render(request, 'admin/core/registration/step2.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 2 - Выбор роли',
            'opts': User._meta,
        })
    
    def post(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или уже завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))
        
        form = Step2RoleForm(request.POST)
        
        if form.is_valid():
            draft.role = form.cleaned_data['role']
            draft.current_step = 2
            draft.save()
            
            messages.success(request, f'Роль "{draft.get_role_display()}" выбрана. Заполните данные роли.')
            return HttpResponseRedirect(reverse('admin:register_step3', args=[draft.id]))
        
        return render(request, 'admin/core/registration/step2.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 2 - Выбор роли',
            'opts': User._meta,
        })

class Step3RegistrationView(RegistrationAdminView):
    """Шаг 3: Заполнение данных роли"""
    
    def get(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или уже завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))
        
        # Выбираем форму в зависимости от роли
        if draft.role == 'trainer':
            form = TrainerForm()
        elif draft.role == 'parent':
            form = ParentForm()
        elif draft.role == 'athlete':
            form = AthleteForm()
        else:
            messages.error(request, 'Неизвестная роль')
            return HttpResponseRedirect(reverse('admin:register_cancel'))
        
        return render(request, 'admin/core/registration/step3.html', {
            'form': form,
            'draft': draft,
            'title': f'Шаг 3 - Данные {draft.get_role_display().lower()}а',
            'opts': User._meta,
        })
    
    def post(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или уже завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))
        
        # Выбираем форму в зависимости от роли
        if draft.role == 'trainer':
            form = TrainerForm(request.POST)
            model_class = Trainer
        elif draft.role == 'parent':
            form = ParentForm(request.POST)
            model_class = Parent
        elif draft.role == 'athlete':
            form = AthleteForm(request.POST)
            model_class = Athlete
        else:
            messages.error(request, 'Неизвестная роль')
            return HttpResponseRedirect(reverse('admin:register_cancel'))
        
        if form.is_valid():
            print(f"Form is valid for {draft.role}")
            # Создаем профиль роли
            profile = form.save(commit=False)
            profile.user = draft.user
            profile.save()
            print(f"Created {draft.role} profile for user {draft.user.username}")
            
            # Активируем пользователя
            draft.user.is_active = True
            draft.user.save()
            print(f"Activated user {draft.user.username}")
            
            # Завершаем черновик
            draft.is_completed = True
            draft.current_step = 3
            draft.save()
            print(f"Completed draft #{draft.id}")
            
            # Очищаем сессию
            request.session.pop('draft_id', None)
            
            # Логируем действие
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(User).pk,
                object_id=draft.user.id,
                object_repr=str(draft.user),
                action_flag=CHANGE,
                change_message=f'Регистрация завершена. Роль: {draft.get_role_display()}'
            )
            
            messages.success(request, f'Регистрация пользователя {draft.user.username} завершена!')
            return HttpResponseRedirect(reverse('admin:register_done'))
        else:
            print(f"Form errors: {form.errors}")
        
        return render(request, 'admin/core/registration/step3.html', {
            'form': form,
            'draft': draft,
            'title': f'Шаг 3 - Данные {draft.get_role_display().lower()}а',
            'opts': User._meta,
        })

class CancelRegistrationView(RegistrationAdminView):
    """Отмена регистрации"""
    
    def get(self, request):
        draft_id = request.session.get('draft_id')
        if draft_id:
            try:
                draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
                draft.safe_dispose()
                messages.info(request, 'Регистрация отменена. Временные данные удалены.')
            except RegistrationDraft.DoesNotExist:
                pass
            request.session.pop('draft_id', None)
        
        return HttpResponseRedirect(reverse('admin:auth_user_changelist'))

class DoneRegistrationView(RegistrationAdminView):
    """Страница завершения регистрации"""
    
    def get(self, request):
        return render(request, 'admin/core/registration/done.html', {
            'title': 'Регистрация завершена',
            'opts': User._meta,
        })

# Кастомный UserAdmin с кнопкой регистрации
class CustomUserAdmin(UserAdmin):
    """Кастомный UserAdmin с кнопкой запуска регистрации"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('register/', Step1RegistrationView.as_view(), name='register_step1'),
            path('register/step2/<int:draft_id>/', Step2RegistrationView.as_view(), name='register_step2'),
            path('register/step3/<int:draft_id>/', Step3RegistrationView.as_view(), name='register_step3'),
            path('register/cancel/', CancelRegistrationView.as_view(), name='register_cancel'),
            path('register/done/', DoneRegistrationView.as_view(), name='register_done'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Добавляем кнопку регистрации в список пользователей"""
        extra_context = extra_context or {}
        extra_context['show_registration_button'] = True
        return super().changelist_view(request, extra_context)

# Регистрируем кастомный UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(RegistrationDraft)
class RegistrationDraftAdmin(admin.ModelAdmin):
    """Админка для мониторинга черновиков регистрации"""
    
    list_display = ('id', 'user', 'role', 'current_step', 'is_completed', 'created_at', 'created_by')
    list_filter = ('is_completed', 'role', 'current_step', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'created_by')
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        return False  # Черновики создаются только через процесс регистрации
    
    def has_change_permission(self, request, obj=None):
        return False  # Черновики нельзя редактировать вручную
    
    def has_delete_permission(self, request, obj=None):
        return True  # Можно удалять для очистки

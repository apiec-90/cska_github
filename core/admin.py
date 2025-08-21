from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, reverse
from django.contrib import messages
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.template.response import TemplateResponse
from django.core.exceptions import PermissionDenied
from django.forms import modelformset_factory
import os
import uuid
from datetime import datetime, timedelta
from django.http import HttpResponseRedirect
from django.contrib.admin.utils import unquote
from django.utils.html import format_html, format_html_join
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .models import (
    PaymentMethod, Staff, Parent, Athlete, Trainer, TrainingGroup, 
    AthleteTrainingGroup, AthleteParent, GroupSchedule, 
    TrainingSession, AttendanceRecord, DocumentType, 
    Document, Payment, AuditRecord, RegistrationDraft
)
from .forms import (
    Step1UserForm,
    Step2RoleForm,
    Step3StaffRoleForm,
    TrainerForm,
    ParentForm,
    AthleteForm,
    StaffForm,
    AthleteProfileForm,
    ParentProfileForm,
    AthleteRelationsForm,
    ParentRelationsForm,
    TrainerRelationsForm,
    GroupScheduleForm
)
from . import utils
from .utils.sessions import ensure_month_sessions_for_group, resync_future_sessions_for_group

# Регистрируем стандартные Django модели
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Inline для связей спортсмен-родитель
class AthleteParentInline(admin.TabularInline):
    """Inline для управления родителями спортсмена"""
    model = AthleteParent
    fk_name = 'athlete'  # связь от спортсмена к родителю
    extra = 1
    verbose_name = "Родитель"
    verbose_name_plural = "Родители"

class AthleteTrainingGroupInline(admin.TabularInline):
    """Inline для управления группами спортсмена"""
    model = AthleteTrainingGroup
    fk_name = 'athlete'
    extra = 0
    verbose_name = "Тренировочная группа"
    verbose_name_plural = "Тренировочные группы"
    fields = ('training_group',)
    autocomplete_fields = ['training_group']

class ParentAthleteInline(admin.TabularInline):
    """Inline для управления детьми родителя"""
    model = AthleteParent
    fk_name = 'parent'  # связь от родителя к спортсмену
    extra = 1
    verbose_name = "Ребенок"
    verbose_name_plural = "Дети"
    fields = ('athlete',)
    autocomplete_fields = ['athlete']

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_phone', 'birth_date', 'get_groups_display', 'get_athletes_count', 'get_active_status', 'is_archived']
    list_filter = ['is_archived', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'phone']
    ordering = ['user__last_name', 'user__first_name']
    
    # Настройка полей для формы
    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'phone', 'birth_date')
        }),
        ('Архивирование', {
            'fields': ('is_archived', 'archived_at', 'archived_by'),
            'classes': ('collapse',),
            'description': 'Настройки архивирования записи'
        }),
    )
    
    # Убираем поле user из формы
    exclude = ('user',)
    
    # Кастомный шаблон
    change_form_template = 'admin/core/trainer/change_form.html'

    def get_full_name(self, obj):
        """Полное имя тренера"""
        first_name = (getattr(obj, 'first_name', None) or obj.user.first_name or "")
        last_name = (getattr(obj, 'last_name', None) or obj.user.last_name or "")
        return f"{last_name} {first_name}".strip() or obj.user.username
    get_full_name.short_description = "ФИО"
    
    def get_phone(self, obj):
        """Телефон тренера"""
        return obj.phone or "—"
    get_phone.short_description = "Телефон"
    
    def get_active_status(self, obj):
        """Статус активности пользователя"""
        if obj.user.is_active:
            return "Активен"
        else:
            return "Неактивен"
    get_active_status.short_description = "Статус"

    def get_groups_count(self, obj):
        """Количество групп тренера"""
        return obj.traininggroup_set.count()
    get_groups_count.short_description = "Групп"

    def get_athletes_count(self, obj):
        """Количество спортсменов в группах тренера"""
        return obj.traininggroup_set.aggregate(
            total=models.Count('athletetraininggroup__athlete', distinct=True)
        )['total'] or 0
    get_athletes_count.short_description = "Спортсменов"
    
    def get_groups_display(self, obj):
        """Отображение групп тренера"""
        groups = obj.traininggroup_set.filter(is_active=True)
        if groups:
            group_names = [group.name for group in groups]
            return ", ".join(group_names)
        return "Групп нет"
    get_groups_display.short_description = "Группы"
    
    def get_queryset(self, request):
        """Оптимизируем запросы"""
        qs = super().get_queryset(request)
        qs = qs.select_related('user').prefetch_related(
            'traininggroup_set'
        )
        return qs
    
    def get_form(self, request, obj=None, **kwargs):
        """Инициализируем форму данными из User если поля пустые"""
        form = super().get_form(request, obj, **kwargs)
        
        if obj and obj.user_id:
            # Если поля Trainer пустые, но есть данные в User, копируем их
            if not obj.first_name and obj.user.first_name:
                obj.first_name = obj.user.first_name
            if not obj.last_name and obj.user.last_name:
                obj.last_name = obj.user.last_name
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Синхронизируем ФИО из Trainer в User"""
        super().save_model(request, obj, form, change)
        
        # Синхронизируем ФИО с User
        if obj.user:
            user = obj.user
            user.first_name = obj.first_name
            user.last_name = obj.last_name
            user.save(update_fields=['first_name', 'last_name'])

    # URLs для загрузок (аватар/документы)
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        trainer_urls = [
            path('<path:object_id>/upload-avatar/', self.admin_site.admin_view(self.upload_avatar), name='%s_%s_upload_avatar' % info),
            path('<path:object_id>/upload-document/', self.admin_site.admin_view(self.upload_document), name='%s_%s_upload_document' % info),
            path('<path:object_id>/delete-document/', self.admin_site.admin_view(self.delete_document), name='%s_%s_delete_document' % info),
        ]
        return trainer_urls + urls

    def upload_avatar(self, request, object_id):
        """Загрузка аватара тренера"""
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        file_obj = request.FILES.get('avatar')
        if not file_obj:
            messages.error(request, 'Файл не выбран')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        try:
            trainer = Trainer.objects.get(pk=object_id)
        except Trainer.DoesNotExist:
            messages.error(request, 'Тренер не найден')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        # Генерируем уникальное имя файла
        file_extension = file_obj.name.split('.')[-1].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
        if file_extension not in allowed_extensions:
            messages.error(request, 'Недопустимый формат файла. Разрешены: JPG, PNG, GIF')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        file_name = f"trainer_{trainer.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        # Сохраняем файл в MEDIA/avatars
        upload_path = os.path.join(settings.MEDIA_ROOT, 'avatars')
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, file_name)
        with open(file_path, 'wb') as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        
        # Создаем запись в Document с типом "Аватар"
        from django.contrib.contenttypes.models import ContentType
        avatar_type, _ = DocumentType.objects.get_or_create(name='Аватар')
        ct = ContentType.objects.get_for_model(Trainer)
        
        # Удаляем предыдущий аватар если есть
        old_avatars = Document.objects.filter(
            content_type=ct, 
            object_id=trainer.id, 
            document_type=avatar_type
        )
        for old_avatar in old_avatars:
            # Удаляем старый файл
            old_file_path = os.path.join(settings.MEDIA_ROOT, old_avatar.file)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
            old_avatar.delete()
        
        # Создаем новую запись
        Document.objects.create(
            document_type=avatar_type,
            content_type=ct,
            object_id=trainer.id,
            file=f'avatars/{file_name}',
            file_type=file_obj.content_type,
            file_size=file_obj.size,
            uploaded_by=request.user,
            comment='Загружен как аватар'
        )
        
        messages.success(request, 'Аватар успешно загружен')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

    def upload_document(self, request, object_id):
        """Загрузка документа тренера"""
        trainer = get_object_or_404(Trainer, pk=object_id)
        if request.method == 'POST' and request.FILES.get('document_file'):
            file_obj = request.FILES['document_file']
            comment = request.POST.get('comment', '')
            document_type_id = request.POST.get('document_type')
            
            # Генерируем уникальное имя файла
            import uuid
            file_extension = file_obj.name.split('.')[-1]
            file_name = f"trainer_{trainer.id}_doc_{uuid.uuid4().hex[:8]}.{file_extension}"
            file_url = f"documents/{file_name}"
            
            # Сохраняем файл
            import os
            from django.conf import settings
            
            upload_path = os.path.join(settings.MEDIA_ROOT, 'documents')
            os.makedirs(upload_path, exist_ok=True)
            
            file_path = os.path.join(upload_path, file_name)
            with open(file_path, 'wb') as f:
                for chunk in file_obj.chunks():
                    f.write(chunk)
            
            # Создаем запись в базе данных
            from django.contrib.contenttypes.models import ContentType
            from core.models import Document, DocumentType
            
            ct_trainer = ContentType.objects.get_for_model(Trainer)
            
            # Получаем или создаем тип документа
            if document_type_id:
                try:
                    doc_type = DocumentType.objects.get(pk=document_type_id)
                except DocumentType.DoesNotExist:
                    doc_type, _ = DocumentType.objects.get_or_create(name='Прочее')
            else:
                doc_type, _ = DocumentType.objects.get_or_create(name='Прочее')
            
            document = Document.objects.create(
                document_type=doc_type,
                content_type=ct_trainer,
                object_id=trainer.id,
                file=file_url,
                file_type=file_obj.content_type,
                file_size=file_obj.size,
                uploaded_by=request.user,
                comment=comment
            )
            
            messages.success(request, 'Документ успешно загружен.')
        
        return redirect('admin:core_trainer_change', object_id=trainer.pk)

    def delete_document(self, request, object_id):
        """Удаление документа тренера"""
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        from core.models import Document
        trainer = get_object_or_404(Trainer, pk=object_id)
        
        if request.method == 'POST':
            document_id = request.POST.get('document_id')
            try:
                document = Document.objects.get(id=document_id)
                
                # Удаляем файл
                import os
                from django.conf import settings
                file_path = os.path.join(settings.MEDIA_ROOT, document.file)
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # Удаляем запись из БД
                document.delete()
                
                messages.success(request, 'Документ успешно удален.')
            except Document.DoesNotExist:
                messages.error(request, 'Документ не найден.')
        
        return redirect('admin:core_trainer_change', object_id=trainer.pk)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Переопределяем для добавления данных в шаблон"""
        from django.shortcuts import get_object_or_404
        from django.contrib.contenttypes.models import ContentType
        from core.models import Document, DocumentType
        
        extra_context = extra_context or {}
        documents = []
        doc_types = DocumentType.objects.all().order_by('name')
        avatar_url = None
        trainer_groups = []
        
        if object_id:
            try:
                trainer = get_object_or_404(Trainer, pk=object_id)
                
                # Получаем группы тренера с дополнительной информацией
                trainer_groups = trainer.traininggroup_set.prefetch_related(
                    'groupschedule_set',
                    'athletetraininggroup_set__athlete'
                ).all()
                
                # Получаем документы тренера
                ct_trainer = ContentType.objects.get_for_model(Trainer)
                documents = Document.objects.filter(
                    content_type=ct_trainer,
                    object_id=trainer.id
                ).select_related('document_type', 'uploaded_by').order_by('-uploaded_at')
                
                # Пробуем найти актуальный аватар из документов
                try:
                    avatar_type = DocumentType.objects.get(name='Аватар')
                    avatar_doc = documents.filter(document_type=avatar_type).first()
                    if avatar_doc:
                        avatar_url = avatar_doc.file
                except DocumentType.DoesNotExist:
                    pass
                
            except Trainer.DoesNotExist:
                pass
        
        extra_context.update({
            'trainer_groups': trainer_groups,
            'trainer_documents': documents,
            'trainer_document_types': doc_types,
            'trainer_avatar_url': avatar_url,
        })
        
        return super().changeform_view(request, object_id, form_url, extra_context)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_role_display', 'get_phone', 'birth_date', 'get_active_status', 'is_archived']
    list_filter = ['role', 'is_archived', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'phone']
    ordering = ['user__last_name', 'user__first_name']
    
    # Настройка полей для формы
    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'phone', 'birth_date', 'role')
        }),
        ('Архивирование', {
            'fields': ('is_archived', 'archived_at', 'archived_by'),
            'classes': ('collapse',),
            'description': 'Настройки архивирования записи'
        }),
    )
    
    # Убираем поле user из формы
    exclude = ('user',)
    
    def get_full_name(self, obj):
        """Полное имя сотрудника"""
        first_name = (getattr(obj, 'first_name', None) or obj.user.first_name or "")
        last_name = (getattr(obj, 'last_name', None) or obj.user.last_name or "")
        return f"{last_name} {first_name}".strip() or obj.user.username
    get_full_name.short_description = "ФИО"
    
    def get_phone(self, obj):
        """Телефон сотрудника"""
        return obj.phone or "—"
    get_phone.short_description = "Телефон"
    
    def get_active_status(self, obj):
        """Статус активности пользователя"""
        if obj.user.is_active:
            return "Активен"
        else:
            return "Неактивен"
    get_active_status.short_description = "Статус"

    def get_role_display(self, obj):
        """Отображение роли сотрудника"""
        return obj.get_role_display()
    get_role_display.short_description = "Роль"
    
    def get_queryset(self, request):
        """Оптимизируем запросы"""
        qs = super().get_queryset(request)
        qs = qs.select_related('user')
        return qs
    
    def get_form(self, request, obj=None, **kwargs):
        """Инициализируем форму данными из User если поля пустые"""
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.user:
            # Если поля first_name или last_name пустые, заполняем из User
            if not obj.first_name and obj.user.first_name:
                form.base_fields['first_name'].initial = obj.user.first_name
            if not obj.last_name and obj.user.last_name:
                form.base_fields['last_name'].initial = obj.user.last_name
        return form
    
    def save_model(self, request, obj, form, change):
        """Синхронизируем ФИО из Staff в User"""
        super().save_model(request, obj, form, change)
        
        # Синхронизируем ФИО с User
        if obj.user:
            user = obj.user
            user.first_name = obj.first_name
            user.last_name = obj.last_name
            user.save(update_fields=['first_name', 'last_name'])

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_phone', 'birth_date', 'get_children_display', 'get_active_status', 'is_archived')
    list_filter = ('is_archived', 'user__is_active')
    search_fields = ('user__first_name', 'user__last_name', 'phone')
    ordering = ('user__last_name', 'user__first_name')
    # # инлайны для управления связями с детьми
    inlines = [ParentAthleteInline]
    # # кастомный шаблон карточки родителя
    change_form_template = 'admin/core/parent/change_form.html'
    
    # Настройка полей для формы
    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'phone', 'birth_date')
        }),
        ('Архивирование', {
            'fields': ('is_archived', 'archived_at', 'archived_by'),
            'classes': ('collapse',),
            'description': 'Настройки архивирования записи'
        }),
    )
    
    # Убираем поле user из формы
    exclude = ('user',)
    
    def get_full_name(self, obj):
        """Полное имя родителя"""
        first_name = (obj.first_name or obj.user.first_name or "")
        last_name = (obj.last_name or obj.user.last_name or "")
        return f"{last_name} {first_name}".strip() or obj.user.username
    get_full_name.short_description = "ФИО"
    
    def get_phone(self, obj):
        """Телефон родителя"""
        return obj.phone or "—"
    get_phone.short_description = "Телефон"
    
    def get_children_display(self, obj):
        """Дети родителя с ФИО"""
        rels = obj.get_children_relations()

        if rels:
            children_names = []
            for rel in rels:
                # Используем ФИО из профиля спортсмена, если есть
                first_name = (rel.athlete.first_name or rel.athlete.user.first_name or "")
                last_name = (rel.athlete.last_name or rel.athlete.user.last_name or "")
                child_name = f"{last_name} {first_name}".strip()
                if not child_name:
                    child_name = rel.athlete.user.username
                children_names.append(child_name)
            return ", ".join(children_names)
        return "Детей нет"
    get_children_display.short_description = "Дети"
    
    def get_active_status(self, obj):
        """Статус активности пользователя"""
        if obj.user.is_active:
            return "Активен"
        else:
            return "Неактивен"
    get_active_status.short_description = "Статус"
    
    def get_queryset(self, request):
        """Оптимизируем запросы"""
        qs = super().get_queryset(request)
        qs = qs.select_related('user').prefetch_related(
            'athleteparent_set__athlete__user'
        )
        return qs
    
    def get_form(self, request, obj=None, **kwargs):
        """Инициализируем форму данными из User если поля пустые"""
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.user:
            # Если поля first_name или last_name пустые, заполняем из User
            if not obj.first_name and obj.user.first_name:
                obj.first_name = obj.user.first_name
            if not obj.last_name and obj.user.last_name:
                obj.last_name = obj.user.last_name
        elif not obj:  # При создании новой записи
            # Если есть user_id в GET параметрах, инициализируем из User
            user_id = request.GET.get('user_id')
            if user_id:
                try:
                    from django.contrib.auth.models import User
                    user = User.objects.get(id=user_id)
                    form.base_fields['first_name'].initial = user.first_name
                    form.base_fields['last_name'].initial = user.last_name
                except User.DoesNotExist:
                    pass
        return form
    
    def save_model(self, request, obj, form, change):
        """Синхронизируем ФИО между Parent и User"""
        super().save_model(request, obj, form, change)
        
        # Синхронизируем ФИО с User
        if obj.user:
            user = obj.user
            user.first_name = obj.first_name
            user.last_name = obj.last_name
            user.save(update_fields=['first_name', 'last_name'])

    # # URLs для загрузок (аватар/документы)
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                '<path:object_id>/upload-avatar/',
                self.admin_site.admin_view(self.upload_avatar),
                name='core_parent_upload_avatar',
            ),
            path(
                '<path:object_id>/upload-document/',
                self.admin_site.admin_view(self.upload_document),
                name='core_parent_upload_document',
            ),
            path(
                '<path:object_id>/delete-document/',
                self.admin_site.admin_view(self.delete_document),
                name='core_parent_delete_document',
            ),
        ]
        return custom + urls

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        documents = []
        doc_types = DocumentType.objects.all().order_by('name')
        avatar_url = None
        if object_id:
            try:
                parent = Parent.objects.get(pk=object_id)
                from django.contrib.contenttypes.models import ContentType
                ct = ContentType.objects.get_for_model(Parent)
                documents = Document.objects.filter(content_type=ct, object_id=parent.id).order_by('-uploaded_at')
                # пробуем найти актуальный аватар из документов
                try:
                    avatar_type = DocumentType.objects.get(name='Аватар')
                    avatar_doc = documents.filter(document_type=avatar_type).first()
                    if avatar_doc:
                        avatar_url = avatar_doc.file
                except DocumentType.DoesNotExist:
                    pass
                
                # # предзагружаем связанные данные для красивого отображения
                parent_children = parent.get_children_relations().select_related(
                    'athlete__user'
                ).prefetch_related(
                    'athlete__athletetraininggroup_set__training_group__trainer__user',
                    'athlete__athletetraininggroup_set__training_group__groupschedule_set'
                )
                
            except Parent.DoesNotExist:
                pass
        extra_context.update({
            'parent_documents': documents,
            'parent_document_types': doc_types,
            'parent_children': parent_children if 'parent_children' in locals() else [],
            'parent_avatar_url': avatar_url,
        })
        return super().changeform_view(request, object_id, form_url, extra_context)

    # # загрузка аватара: сохраняем файл в MEDIA/avatars и пишем путь в parent.photo + создаем Document
    def upload_avatar(self, request, object_id):
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        file_obj = request.FILES.get('avatar')
        if not file_obj:
            messages.error(request, 'Файл не выбран')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        try:
            parent = Parent.objects.get(pk=object_id)
        except Parent.DoesNotExist:
            messages.error(request, 'Родитель не найден')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

        # Удаляем предыдущий файл аватара (если был) и документы типа "Аватар"
        try:
            # Удаляем старые документы-аватары
            from django.contrib.contenttypes.models import ContentType
            avatar_type, _ = DocumentType.objects.get_or_create(name='Аватар')
            ct_parent = ContentType.objects.get_for_model(Parent)
            old_docs = Document.objects.filter(document_type=avatar_type, content_type=ct_parent, object_id=parent.id)
            for d in old_docs:
                try:
                    file_url = str(d.file)
                    media_root = getattr(settings, 'MEDIA_ROOT', 'media')
                    media_url = getattr(settings, 'MEDIA_URL', '/media/')
                    if file_url.startswith(media_url):
                        rel = file_url[len(media_url):]
                    elif '/media/' in file_url:
                        rel = file_url.split('/media/', 1)[1]
                    else:
                        rel = file_url.lstrip('/')
                    file_path = os.path.join(media_root, rel)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Ошибка удаления файла: {e}")
                d.delete()
        except Exception as e:
            print(f"Ошибка очистки старых аватаров: {e}")

        # Сохраняем новый файл
        try:
            # Создаем директорию если не существует
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            avatars_dir = os.path.join(media_root, 'avatars')
            os.makedirs(avatars_dir, exist_ok=True)
            
            # Генерируем уникальное имя файла
            file_ext = os.path.splitext(file_obj.name)[1]
            filename = f"parent_{parent.id}_{uuid.uuid4().hex[:8]}{file_ext}"
            file_path = os.path.join(avatars_dir, filename)
            
            # Сохраняем файл
            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
            
            # Создаем Document
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            file_url = f"{media_url}avatars/{filename}"
            
            document = Document.objects.create(
                document_type=avatar_type,
                content_type=ct_parent,
                object_id=parent.id,
                file=file_url,
                file_type=file_obj.content_type,
                file_size=file_obj.size,
                uploaded_by=request.user,
                comment="Аватар родителя"
            )
            
            messages.success(request, 'Аватар успешно загружен')
        except Exception as e:
            messages.error(request, f'Ошибка загрузки аватара: {e}')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

    def upload_document(self, request, object_id):
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        file_obj = request.FILES.get('document_file')
        document_type_id = request.POST.get('document_type')
        comment = request.POST.get('comment', '')
        
        if not file_obj:
            messages.error(request, 'Файл не выбран')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        try:
            parent = Parent.objects.get(pk=object_id)
        except Parent.DoesNotExist:
            messages.error(request, 'Родитель не найден')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

        try:
            # Создаем директорию если не существует
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            documents_dir = os.path.join(media_root, 'documents')
            os.makedirs(documents_dir, exist_ok=True)
            
            # Генерируем уникальное имя файла
            file_ext = os.path.splitext(file_obj.name)[1]
            filename = f"parent_{parent.id}_{uuid.uuid4().hex[:8]}{file_ext}"
            file_path = os.path.join(documents_dir, filename)
            
            # Сохраняем файл
            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
            
            # Создаем Document
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            file_url = f"{media_url}documents/{filename}"
            
            from django.contrib.contenttypes.models import ContentType
            ct_parent = ContentType.objects.get_for_model(Parent)
            
            # Получаем или создаем тип документа
            if document_type_id:
                try:
                    doc_type = DocumentType.objects.get(pk=document_type_id)
                except DocumentType.DoesNotExist:
                    doc_type, _ = DocumentType.objects.get_or_create(name='Прочее')
            else:
                doc_type, _ = DocumentType.objects.get_or_create(name='Прочее')
            
            document = Document.objects.create(
                document_type=doc_type,
                content_type=ct_parent,
                object_id=parent.id,
                file=file_url,
                file_type=file_obj.content_type,
                file_size=file_obj.size,
                uploaded_by=request.user,
                comment=comment
            )
            
            messages.success(request, 'Документ успешно загружен')
        except Exception as e:
            messages.error(request, f'Ошибка загрузки документа: {e}')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

    def delete_document(self, request, object_id):
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        document_id = request.POST.get('document_id')
        if not document_id:
            messages.error(request, 'ID документа не указан')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        try:
            document = Document.objects.get(pk=document_id)
            
            # Удаляем файл
            try:
                file_url = str(document.file)
                media_root = getattr(settings, 'MEDIA_ROOT', 'media')
                media_url = getattr(settings, 'MEDIA_URL', '/media/')
                if file_url.startswith(media_url):
                    rel = file_url[len(media_url):]
                elif '/media/' in file_url:
                    rel = file_url.split('/media/', 1)[1]
                else:
                    rel = file_url.lstrip('/')
                file_path = os.path.join(media_root, rel)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Ошибка удаления файла: {e}")
            
            document.delete()
            messages.success(request, 'Документ успешно удален')
        except Document.DoesNotExist:
            messages.error(request, 'Документ не найден')
        except Exception as e:
            messages.error(request, f'Ошибка удаления документа: {e}')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
    


@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_phone', 'birth_date', 'get_groups_display', 'get_parents_display', 'get_active_status', 'is_archived')
    list_filter = ('is_archived', 'birth_date', 'user__is_active')
    search_fields = ('user__first_name', 'user__last_name', 'phone')
    ordering = ('user__last_name', 'user__first_name')
    # # инлайны для управления связями с родителями и группами
    inlines = [AthleteParentInline, AthleteTrainingGroupInline]
    # # кастомный шаблон карточки спортсмена
    change_form_template = 'admin/core/athlete/change_form.html'
    
    # Настройка полей для формы
    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'birth_date', 'phone')
        }),
        ('Архивирование', {
            'fields': ('is_archived', 'archived_at', 'archived_by'),
            'classes': ('collapse',),
            'description': 'Настройки архивирования записи'
        }),
    )
    
    # Убираем поле user из формы
    exclude = ('user',)
    
    def get_readonly_fields(self, request, obj=None):
        """Делаем поле user только для чтения"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:  # Только для существующих записей
            readonly_fields.append('user')
        return readonly_fields
    
    def get_form(self, request, obj=None, **kwargs):
        """Инициализируем форму с данными из связанного пользователя"""
        form = super().get_form(request, obj, **kwargs)
        
        if obj and obj.user_id:
            # Если поля Athlete пустые, но есть данные в User, копируем их
            if not obj.first_name and obj.user.first_name:
                obj.first_name = obj.user.first_name
            if not obj.last_name and obj.user.last_name:
                obj.last_name = obj.user.last_name
        
        return form

    # # URLs для загрузок (аватар/документы)
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                '<path:object_id>/upload-avatar/',
                self.admin_site.admin_view(self.upload_avatar),
                name='core_athlete_upload_avatar',
            ),
            path(
                '<path:object_id>/upload-document/',
                self.admin_site.admin_view(self.upload_document),
                name='core_athlete_upload_document',
            ),
            path(
                '<path:object_id>/delete-document/',
                self.admin_site.admin_view(self.delete_document),
                name='core_athlete_delete_document',
            ),
        ]
        return custom + urls

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        documents = []
        doc_types = DocumentType.objects.all().order_by('name')
        avatar_url = None
        if object_id:
            try:
                athlete = Athlete.objects.get(pk=object_id)
                from django.contrib.contenttypes.models import ContentType
                ct = ContentType.objects.get_for_model(Athlete)
                documents = Document.objects.filter(content_type=ct, object_id=athlete.id).order_by('-uploaded_at')
                # пробуем найти актуальный аватар из документов
                try:
                    avatar_type = DocumentType.objects.get(name='Аватар')
                    avatar_doc = documents.filter(document_type=avatar_type).first()
                    if avatar_doc:
                        avatar_url = avatar_doc.file
                except DocumentType.DoesNotExist:
                    pass
                
                # # предзагружаем связанные данные для красивого отображения
                athlete_groups = athlete.athletetraininggroup_set.select_related(
                    'training_group__trainer__user'
                ).prefetch_related(
                    'training_group__groupschedule_set'
                ).all()
                
                athlete_parents = athlete.athleteparent_set.select_related(
                    'parent__user'
                ).all()
                
            except Athlete.DoesNotExist:
                pass
        extra_context.update({
            'athlete_documents': documents,
            'athlete_document_types': doc_types,
            'athlete_groups': athlete_groups if 'athlete_groups' in locals() else [],
            'athlete_parents': athlete_parents if 'athlete_parents' in locals() else [],
            'athlete_avatar_url': avatar_url,
        })
        return super().changeform_view(request, object_id, form_url, extra_context)

    # # загрузка аватара: сохраняем файл в MEDIA/avatars и пишем путь в athlete.photo + создаем Document
    def upload_avatar(self, request, object_id):
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        file_obj = request.FILES.get('avatar')
        if not file_obj:
            messages.error(request, 'Файл не выбран')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        try:
            athlete = Athlete.objects.get(pk=object_id)
        except Athlete.DoesNotExist:
            messages.error(request, 'Спортсмен не найден')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

        # Удаляем предыдущий файл аватара (если был) и документы типа "Аватар"
        try:
            if athlete.photo:
                prev_url = str(athlete.photo)
                media_root = getattr(settings, 'MEDIA_ROOT', 'media')
                media_url = getattr(settings, 'MEDIA_URL', '/media/')
                if prev_url.startswith(media_url):
                    rel_prev = prev_url[len(media_url):]
                elif '/media/' in prev_url:
                    rel_prev = prev_url.split('/media/', 1)[1]
                else:
                    rel_prev = prev_url.lstrip('/')
                prev_path = os.path.join(media_root, rel_prev)
                if os.path.exists(prev_path):
                    os.remove(prev_path)
            # Удаляем старые документы-аватары
            from django.contrib.contenttypes.models import ContentType
            avatar_type, _ = DocumentType.objects.get_or_create(name='Аватар')
            ct_athlete = ContentType.objects.get_for_model(Athlete)
            old_docs = Document.objects.filter(document_type=avatar_type, content_type=ct_athlete, object_id=athlete.id)
            for d in old_docs:
                try:
                    file_url = str(d.file)
                    media_root = getattr(settings, 'MEDIA_ROOT', 'media')
                    media_url = getattr(settings, 'MEDIA_URL', '/media/')
                    if file_url.startswith(media_url):
                        rel = file_url[len(media_url):]
                    elif '/media/' in file_url:
                        rel = file_url.split('/media/', 1)[1]
                    else:
                        rel = file_url.lstrip('/')
                    file_path = os.path.join(media_root, rel)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass
            old_docs.delete()
        except Exception:
            pass

        ext = os.path.splitext(file_obj.name)[1].lower() or '.bin'
        filename = f"{uuid.uuid4().hex}{ext}"
        folder = os.path.join(getattr(settings, 'MEDIA_ROOT', 'media'), 'avatars')
        os.makedirs(folder, exist_ok=True)
        fs_path = os.path.join(folder, filename)
        with open(fs_path, 'wb') as out:
            for chunk in file_obj.chunks():
                out.write(chunk)
        url = f"{getattr(settings, 'MEDIA_URL', '/media/') }avatars/{filename}"

        # фото в профиль не пишем — только документ и предпросмотр из документов

        # создаем запись документа
        from django.contrib.contenttypes.models import ContentType
        doc_type, _ = DocumentType.objects.get_or_create(name='Аватар')
        Document.objects.create(
            file=url,
            file_type=ext.lstrip('.'),
            file_size=getattr(file_obj, 'size', 0),
            document_type=doc_type,
            content_type=ContentType.objects.get_for_model(Athlete),
            object_id=athlete.id,
            uploaded_by=request.user,
            is_private=False,
            comment='Загружен как аватар',
        )

        messages.success(request, 'Аватар обновлён')
        return HttpResponseRedirect(reverse('admin:core_athlete_change', args=[athlete.id]))

    # # загрузка произвольного документа
    def upload_document(self, request, object_id):
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        file_obj = request.FILES.get('document_file')
        doc_type_id = request.POST.get('document_type')
        comment = request.POST.get('comment', '')
        if not file_obj:
            messages.error(request, 'Файл не выбран')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        try:
            athlete = Athlete.objects.get(pk=object_id)
        except Athlete.DoesNotExist:
            messages.error(request, 'Спортсмен не найден')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

        ext = os.path.splitext(file_obj.name)[1].lower() or '.bin'
        filename = f"{uuid.uuid4().hex}{ext}"
        folder = os.path.join(getattr(settings, 'MEDIA_ROOT', 'media'), 'documents')
        os.makedirs(folder, exist_ok=True)
        fs_path = os.path.join(folder, filename)
        with open(fs_path, 'wb') as out:
            for chunk in file_obj.chunks():
                out.write(chunk)
        url = f"{getattr(settings, 'MEDIA_URL', '/media/') }documents/{filename}"

        from django.contrib.contenttypes.models import ContentType
        if doc_type_id:
            try:
                doc_type = DocumentType.objects.get(pk=doc_type_id)
            except DocumentType.DoesNotExist:
                doc_type = DocumentType.objects.create(name='Прочее')
        else:
            doc_type, _ = DocumentType.objects.get_or_create(name='Прочее')

        Document.objects.create(
            file=url,
            file_type=ext.lstrip('.'),
            file_size=getattr(file_obj, 'size', 0),
            document_type=doc_type,
            content_type=ContentType.objects.get_for_model(Athlete),
            object_id=athlete.id,
            uploaded_by=request.user,
            is_private=False,
            comment=comment,
        )
        messages.success(request, 'Документ загружен')
        return HttpResponseRedirect(reverse('admin:core_athlete_change', args=[athlete.id]))
    
    def delete_document(self, request, object_id):
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        document_id = request.POST.get('document_id')
        if not document_id:
            messages.error(request, 'ID документа не указан')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        try:
            athlete = Athlete.objects.get(pk=object_id)
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(Athlete)
            document = Document.objects.get(
                id=document_id,
                content_type=ct,
                object_id=athlete.id
            )
            
            # Удаляем файл с диска
            if document.file:
                try:
                    media_root = getattr(settings, 'MEDIA_ROOT', 'media')
                    media_url = getattr(settings, 'MEDIA_URL', '/media/')
                    file_url = str(document.file)
                    # Преобразуем URL/относительный путь в физический путь
                    if file_url.startswith(media_url):
                        rel_path = file_url[len(media_url):]
                    elif '/media/' in file_url:
                        rel_path = file_url.split('/media/', 1)[1]
                    else:
                        rel_path = file_url.lstrip('/')
                    file_path = os.path.join(media_root, rel_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    messages.warning(request, f'Файл не удален с диска: {e}')
            
            # Удаляем запись из БД
            document.delete()
            messages.success(request, 'Документ удален')
            
        except Athlete.DoesNotExist:
            messages.error(request, 'Спортсмен не найден')
        except Document.DoesNotExist:
            messages.error(request, 'Документ не найден')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {e}')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
    
    def get_full_name(self, obj):
        """Полное имя спортсмена"""
        # Приоритет: поля модели Athlete, затем User
        first_name = (obj.first_name or obj.user.first_name or "")
        last_name = (obj.last_name or obj.user.last_name or "")
        return f"{last_name} {first_name}".strip() or obj.user.username
    get_full_name.short_description = "ФИО"
    
    def get_phone(self, obj):
        """Телефон спортсмена"""
        return obj.phone or "—"
    get_phone.short_description = "Телефон"
    
    def get_groups_display(self, obj):
        """Группы спортсмена"""
        groups = obj.athletetraininggroup_set.select_related('training_group').all()
        if groups:
            group_names = [group.training_group.name for group in groups]
            return ", ".join(group_names)
        return "Не указаны"
    get_groups_display.short_description = "Группы"
    
    def get_parents_display(self, obj):
        """Отображение родителей в списке"""
        parents = obj.get_parents()
        if parents:
            parent_names = []
            for parent in parents:
                first_name = parent.parent.user.first_name or ""
                last_name = parent.parent.user.last_name or ""
                full_name = f"{last_name} {first_name}".strip() or parent.parent.user.username
                parent_names.append(full_name)
            return ", ".join(parent_names)
        return "Не указаны"
    get_parents_display.short_description = "Родители"
    
    def get_active_status(self, obj):
        """Статус активности пользователя"""
        if obj.user.is_active:
            return "Активен"
        else:
            return "Неактивен"
    get_active_status.short_description = "Статус"
    
    def get_queryset(self, request):
        """Оптимизируем запросы"""
        qs = super().get_queryset(request)
        qs = qs.select_related('user').prefetch_related(
            'athletetraininggroup_set__training_group',
            'athleteparent_set__parent__user'
        )
        return qs
    
    def save_model(self, request, obj, form, change):
        """Синхронизируем ФИО с пользователем при сохранении"""
        super().save_model(request, obj, form, change)
        
        # Если есть связанный пользователь, синхронизируем ФИО
        if obj.user_id:
            user = obj.user
            # Синхронизируем ФИО в обе стороны
            if obj.first_name:
                user.first_name = obj.first_name
            if obj.last_name:
                user.last_name = obj.last_name
            user.save(update_fields=['first_name', 'last_name'])

# Исправленный админ для TrainingGroup перенесен в конец файла


# Убираем AthleteTrainingGroup из основного меню админки, но оставляем для inline в филдсетах
# @admin.register(AthleteTrainingGroup)
# class AthleteTrainingGroupAdmin(admin.ModelAdmin):
#     list_display = ('athlete', 'training_group')
#     list_filter = ('training_group',)
#     search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'training_group__name')
#     ordering = ('athlete__user__last_name', 'training_group__name')

# Убираем AthleteParent из основного меню админки, но оставляем для inline в филдсетах
# @admin.register(AthleteParent)
# class AthleteParentAdmin(admin.ModelAdmin):
#     list_display = ('athlete', 'parent')
#     list_filter = ('parent',)
#     search_fields = ('athlete__user__first_name', 'athlete__user__last_name', 'parent__user__first_name', 'parent__user__last_name')
#     ordering = ('athlete__user__last_name', 'parent__user__last_name)

# Убираем GroupSchedule из основного меню админки, но оставляем для inline в филдсетах
# class GroupScheduleAdmin(admin.ModelAdmin):
#     form = GroupScheduleForm
#     list_display = ('training_group', 'get_weekday_display', 'start_time', 'end_time')
#     list_filter = ('training_group', 'weekday')
#     search_fields = ('training_group__name',)
#     ordering = ('training_group__name', 'weekday', 'start_time')
#     
#     def get_form(self, request, obj=None, **kwargs):
#         """Переопределяем для предзаполнения группы из GET параметров"""
#         form = super().get_form(request, obj, **kwargs)
#         
#         # Если создаем новую запись и есть параметр training_group в GET
#         if not obj and 'training_group' in request.GET:
#             try:
#                 training_group_id = int(request.GET['training_group'])
#                 training_group = TrainingGroup.objects.get(pk=training_group_id)
#                 form.base_fields['training_group'].initial = training_group
#             except (ValueError, TrainingGroup.DoesNotExist):
#                 pass
#         
#         return form
#     
#     def save_model(self, request, obj, form, change):
#         """Переопределяем сохранение модели для работы с множественными днями"""
#         # Вызываем метод save формы, который обрабатывает множественные дни
#         form.save()
#     
#     def get_weekday_display(self, obj):
#         """Отображение дня недели с цветной меткой"""
#         weekday_names = {
#             1: ('Понедельник', '#2196F3'),
#             2: ('Вторник', '#4CAF50'), 
#             3: ('Среда', '#FF9800'),
#             4: ('Четверг', '#9C27B0'),
#             5: ('Пятница', '#F44336'),
#             6: ('Суббота', '#607D8B'),
#             7: ('Воскресенье', '#795548')
#         }
#         name, color = weekday_names.get(obj.weekday, (f'День {obj.weekday}', '#666'))
#         return format_html(
#             '<span style="display: inline-block; width: 12px; height: 12px; background-color: {}; border-radius: 50%; margin-right: 8px;"></span>{}',
#             color, name
#         )
#     get_weekday_display.short_description = 'День недели'
#     
#     def response_add(self, request, obj, post_url_override=None):
#         """Кастомное сообщение после добавления"""
#         # Получаем данные из POST запроса
#         if request.method == 'POST':
#             form = self.get_form(request)(request.POST)
#             if form.is_valid():
#                 training_group = form.cleaned_data.get('training_group')
#                 weekdays = form.cleaned_data.get('weekdays', [])
#                 start_time = form.cleaned_data.get('start_time')
#         
#                 if training_group and weekdays:
#                     count = len(weekdays)
#                     if count > 1:
#                         messages.success(
#                             request, 
#                             f'Успешно создано расписание для {count} дней недели для группы "{training_group}"'
#                         )
#                     else:
#                         messages.success(
#                             request, 
#                             f'Успешно создано расписание для группы "{training_group}"'
#                         )
#         
#         return super().response_add(request, obj, post_url_override)
#     
#     def response_change(self, request, obj):
#         """Кастомное сообщение после изменения"""
#         # Получаем данные из POST запроса
#         if request.method == 'POST':
#             form = self.get_form(request, obj)(request.POST, instance=obj)
#             if form.is_valid():
#                 training_group = form.cleaned_data.get('training_group')
#                 weekdays = form.cleaned_data.get('weekdays', [])
#                 start_time = form.cleaned_data.get('start_time')
#                 
#                 if training_group and weekdays:
#                     count = len(weekdays)
#                     messages.success(
#                         request, 
#                         f'Расписание обновлено. Активно расписаний: {count} для группы "{training_group}"'
#                         )
#         
#         return super().response_change(request, obj)

# Inline для записей посещаемости в сессии
class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ('athlete', 'was_present', 'marked_by')
    readonly_fields = ('marked_by',)

# TrainingSession скрыта из меню - управляем через TrainingGroup
try:
    admin.site.unregister(TrainingSession)
except admin.sites.NotRegistered:
    pass

class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('training_group', 'date', 'start_time', 'end_time', 'is_closed', 'is_canceled')
    list_filter = ('training_group', 'date', 'is_closed', 'is_canceled')
    search_fields = ('training_group__name',)
    ordering = ('-date', 'training_group__name')
    inlines = [AttendanceRecordInline]

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
            role = form.cleaned_data['role']
            draft.role = role
            draft.current_step = 2
            draft.save()
            
            # Назначаем базовую группу по роли
            utils.assign_groups_for_registration(draft.user, role)
            
            # если сотрудник — идем на выбор подроли (шаг 3а)
            if draft.role == 'staff':
                draft.current_step = 3
                draft.save()
                return HttpResponseRedirect(reverse('admin:register_step3_staff', args=[draft.id]))
            # иначе шаг 3 — профиль
            draft.current_step = 3
            draft.save()
            return HttpResponseRedirect(reverse('admin:register_step3_profile', args=[draft.id]))
        
        return render(request, 'admin/core/registration/step2.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 2 - Выбор роли',
            'opts': User._meta,
        })

class Step3StaffRoleView(RegistrationAdminView):
    """Шаг 3: Выбор подроли сотрудника (только для staff)"""
    
    def get(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или уже завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))
        
        if draft.role != 'staff':
            messages.error(request, 'Этот шаг доступен только для сотрудников.')
            return HttpResponseRedirect(reverse('admin:register_step1'))

        form = Step3StaffRoleForm(initial={'staff_role': draft.staff_role})

        return render(request, 'admin/core/registration/step3_staff_role.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 3 - Выбор подроли сотрудника',
            'opts': User._meta,
        })
    
    def post(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или уже завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))
        
        if draft.role != 'staff':
            messages.error(request, 'Этот шаг доступен только для сотрудников.')
            return HttpResponseRedirect(reverse('admin:register_step1'))

        form = Step3StaffRoleForm(request.POST)
        if form.is_valid():
            subrole = form.cleaned_data['staff_role']
            draft.staff_role = subrole
            draft.current_step = 4
            draft.save()
            
            # Назначаем группу подроли для staff
            utils.assign_groups_for_registration(draft.user, 'staff', subrole)
            
            return HttpResponseRedirect(reverse('admin:register_step4', args=[draft.id]))
        return render(request, 'admin/core/registration/step3_staff_role.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 3 - Выбор подроли сотрудника',
            'opts': User._meta,
        })


class Step3ProfileView(RegistrationAdminView):
    """Шаг 3: Профиль для athlete/parent/trainer"""
    def get(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))

        if draft.role == 'athlete':
            form = AthleteProfileForm(initial={
                'first_name': draft.user.first_name,
                'last_name': draft.user.last_name,
            })
        elif draft.role == 'parent':
            form = ParentProfileForm(initial={
                'first_name': draft.user.first_name,
                'last_name': draft.user.last_name,
            })
        elif draft.role == 'trainer':
            form = TrainerForm()
        else:
            return HttpResponseRedirect(reverse('admin:register_step3_staff', args=[draft.id]))

        return render(request, 'admin/core/registration/step3_profile.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 3 - Данные профиля',
            'opts': User._meta,
        })

    def post(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))

        if draft.role == 'athlete':
            form = AthleteProfileForm(request.POST)
            if form.is_valid():
                # # сохраняем ФИО на User, создаем Athlete
                draft.user.first_name = form.cleaned_data['first_name']
                draft.user.last_name = form.cleaned_data['last_name']
                draft.user.save()
                Athlete.objects.create(
                    user=draft.user,
                    birth_date=form.cleaned_data['birth_date'],
                    phone=form.cleaned_data['phone'],  # Убираем .get() с дефолтом
                    first_name=form.cleaned_data['first_name'],  # Сохраняем ФИО в профиль
                    last_name=form.cleaned_data['last_name']
                )
                draft.current_step = 4
                draft.save()
                return HttpResponseRedirect(reverse('admin:register_step4_relations', args=[draft.id]))
        elif draft.role == 'parent':
            form = ParentProfileForm(request.POST)
            if form.is_valid():
                draft.user.first_name = form.cleaned_data['first_name']
                draft.user.last_name = form.cleaned_data['last_name']
                draft.user.save()
                # Создаем запись Parent с данными профиля
                Parent.objects.create(
                    user=draft.user,
                    phone=form.cleaned_data['phone'],  # Убираем .get() с дефолтом
                    first_name=form.cleaned_data['first_name'],  # Сохраняем ФИО в профиль
                    last_name=form.cleaned_data['last_name']
                )
                draft.current_step = 4
                draft.save()
                return HttpResponseRedirect(reverse('admin:register_step4_relations', args=[draft.id]))
        elif draft.role == 'trainer':
            form = TrainerForm(request.POST)
            if form.is_valid():
                # Сохраняем ФИО в User
                draft.user.first_name = form.cleaned_data['first_name']
                draft.user.last_name = form.cleaned_data['last_name']
                draft.user.save()
                
                # Создаем профиль тренера
                profile = form.save(commit=False)
                profile.user = draft.user
                profile.save()
                draft.current_step = 4
                draft.save()
                return HttpResponseRedirect(reverse('admin:register_step4_relations', args=[draft.id]))
        else:
            return HttpResponseRedirect(reverse('admin:register_step1'))

        return render(request, 'admin/core/registration/step3_profile.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 3 - Данные профиля',
            'opts': User._meta,
        })

class Step4ProfileView(RegistrationAdminView):
    """Шаг 4: Заполнение профиля по выбранной роли"""

    def get(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или уже завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))

        # Только staff попадает сюда; остальные уходят на связи
        if draft.role != 'staff':
            return HttpResponseRedirect(reverse('admin:register_step4_relations', args=[draft.id]))

        if draft.role == 'staff':
            # На шаге 4 профиль без выбора роли/подроли
            from .forms import StaffRegisterProfileForm
            form = StaffRegisterProfileForm()
        else:
            # Для не-staff ролей профили уже созданы на шаге 3
            messages.error(request, f'Для роли {draft.get_role_display()} профиль уже создан на шаге 3')
            return HttpResponseRedirect(reverse('admin:register_step4_relations', args=[draft.id]))

        return render(request, 'admin/core/registration/step4.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 4 - Данные профиля',
            'opts': User._meta,
        })

    def post(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или уже завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))

        if draft.role != 'staff':
            return HttpResponseRedirect(reverse('admin:register_step4_relations', args=[draft.id]))

        if draft.role == 'staff':
            from .forms import StaffRegisterProfileForm
            form = StaffRegisterProfileForm(request.POST)
        else:
            # Для не-staff ролей профили уже созданы на шаге 3
            messages.error(request, f'Для роли {draft.get_role_display()} профиль уже создан на шаге 3')
            return HttpResponseRedirect(reverse('admin:register_step4_relations', args=[draft.id]))

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = draft.user
            profile.save()

            draft.user.is_active = True
            draft.user.save()

            draft.is_completed = True
            draft.current_step = 4
            draft.save()

            request.session.pop('draft_id', None)

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

        return render(request, 'admin/core/registration/step4.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 4 - Данные профиля',
            'opts': User._meta,
        })


class Step4RelationsView(RegistrationAdminView):
    """Шаг 4: Связи для athlete/parent/trainer (необязательно)."""
    def get(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или уже завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))

        if draft.role == 'athlete':
            form = AthleteRelationsForm()
        elif draft.role == 'parent':
            form = ParentRelationsForm()
        elif draft.role == 'trainer':
            form = TrainerRelationsForm()
        else:
            return HttpResponseRedirect(reverse('admin:register_step4', args=[draft.id]))

        return render(request, 'admin/core/registration/step4_relations.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 4 - Связи (необязательно)',
            'opts': User._meta,
        })

    def post(self, request, draft_id):
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Черновик #{draft_id} не найден или уже завершен.')
            return HttpResponseRedirect(reverse('admin:register_step1'))

        # Пропуск связей
        if '_skip' in request.POST:
            draft.user.is_active = True
            draft.user.save()
            draft.is_completed = True
            draft.current_step = 4
            draft.save()
            request.session.pop('draft_id', None)
            messages.success(request, f'Регистрация {draft.user.username} завершена (связи пропущены).')
            return HttpResponseRedirect(reverse('admin:register_done'))

        # Сохранение связей по ролям
        if draft.role == 'athlete':
            form = AthleteRelationsForm(request.POST)
            if form.is_valid():
                # Проверяем существование профиля, если нет - создаем базовый
                try:
                    athlete = Athlete.objects.get(user=draft.user)
                except Athlete.DoesNotExist:
                    # Создаем базовый профиль спортсмена с временными данными
                    athlete = Athlete.objects.create(
                        user=draft.user,
                        birth_date=timezone.now().date(),
                        phone=f'athlete_{draft.user.id}_{timezone.now().strftime("%Y%m%d")}',
                        first_name=draft.user.first_name or 'Имя',  # Берем из User или дефолт
                        last_name=draft.user.last_name or 'Фамилия'
                    )
                    messages.warning(request, 'Создан базовый профиль спортсмена. Заполните данные позже.')
                
                groups = list(form.cleaned_data['groups'])
                AthleteTrainingGroup.objects.filter(athlete=athlete).delete()
                AthleteTrainingGroup.objects.bulk_create([
                    AthleteTrainingGroup(athlete=athlete, training_group=g) for g in groups
                ])
            else:
                return render(request, 'admin/core/registration/step4_relations.html', {
                    'form': form, 'draft': draft, 'title': 'Шаг 4 - Связи (необязательно)', 'opts': User._meta,
                })
        elif draft.role == 'parent':
            form = ParentRelationsForm(request.POST)
            if form.is_valid():
                # Проверяем существование профиля, если нет - создаем базовый
                try:
                    parent = Parent.objects.get(user=draft.user)
                except Parent.DoesNotExist:
                    # Создаем базовый профиль родителя с временными данными
                    parent = Parent.objects.create(
                        user=draft.user,
                        phone=f'parent_{draft.user.id}_{timezone.now().strftime("%Y%m%d")}',
                        first_name=draft.user.first_name or 'Имя',  # Берем из User или дефолт
                        last_name=draft.user.last_name or 'Фамилия'
                    )
                    messages.warning(request, 'Создан базовый профиль родителя. Заполните данные позже.')
                
                children = list(form.cleaned_data['children'])
                AthleteParent.objects.filter(parent=parent).delete()
                AthleteParent.objects.bulk_create([
                    AthleteParent(parent=parent, athlete=child) for child in children
                ])
            else:
                return render(request, 'admin/core/registration/step4_relations.html', {
                    'form': form, 'draft': draft, 'title': 'Шаг 4 - Связи (необязательно)', 'opts': User._meta,
                })
        elif draft.role == 'trainer':
            form = TrainerRelationsForm(request.POST)
            if form.is_valid():
                # Проверяем существование профиля, если нет - создаем базовый
                try:
                    trainer = Trainer.objects.get(user=draft.user)
                except Trainer.DoesNotExist:
                    # Создаем базовый профиль тренера с временными данными
                    trainer = Trainer.objects.create(
                        user=draft.user,
                        birth_date=timezone.now().date(),
                        phone=f'trainer_{draft.user.id}_{timezone.now().strftime("%Y%m%d")}',
                        first_name=draft.user.first_name or 'Имя',  # Берем из User или дефолт
                        last_name=draft.user.last_name or 'Фамилия'
                    )
                    messages.warning(request, 'Создан базовый профиль тренера. Заполните данные позже.')
                
                groups = list(form.cleaned_data['groups'])
                # # выбираем только свободные группы и назначаем текущего тренера
                for g in groups:
                    if g.trainer_id is None:
                        g.trainer = trainer
                        g.save()
            else:
                return render(request, 'admin/core/registration/step4_relations.html', {
                    'form': form, 'draft': draft, 'title': 'Шаг 4 - Связи (необязательно)', 'opts': User._meta,
                })
        else:
            return HttpResponseRedirect(reverse('admin:register_step4', args=[draft.id]))

        # Завершение
        draft.user.is_active = True
        draft.user.save()
        draft.is_completed = True
        draft.current_step = 4
        draft.save()
        request.session.pop('draft_id', None)
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
    
    # Убираем стандартные горизонтальные множественные для groups/permissions
    filter_horizontal = ()  # Не инициализируем SelectFilter для скрытых полей
    
    def get_phone(self, obj):
        """Получаем телефон пользователя из профилей"""
        try:
            # Проверяем все возможные профили
            if hasattr(obj, 'trainer') and obj.trainer.phone:
                return obj.trainer.phone
            elif hasattr(obj, 'parent') and obj.parent.phone:
                return obj.parent.phone
            elif hasattr(obj, 'athlete') and obj.athlete.phone:
                return obj.athlete.phone
            elif hasattr(obj, 'staff') and obj.staff.phone:
                return obj.staff.phone
            else:
                return "—"
        except:
            return "—"
    get_phone.short_description = "Телефон"
    
    def get_user_groups(self, obj):
        """Получаем группы пользователя"""
        groups = obj.groups.all().order_by('name')
        if groups.exists():
            return ", ".join(g.name for g in groups)
        return "—"
    get_user_groups.short_description = "Группы"
    
    def permissions_summary(self, obj):
        """Текстовая сводка: группы и права через группы"""
        if not obj:
            return "-"
        groups = obj.groups.all().order_by('name')
        # Права через группы
        perms = Permission.objects.filter(group__in=groups).select_related('content_type').distinct()\
            .order_by('content_type__app_label', 'content_type__model', 'name')

        groups_str = ", ".join(g.name for g in groups) if groups.exists() else "—"
        items = [(f"{p.content_type.app_label} | {p.content_type.model} | {p.name}",) for p in perms]
        perms_html = format_html("<ul>{}</ul>",
                                 format_html_join("", "<li>{}</li>", items) if items else format_html("<li>—</li>"))
        return format_html(
            "<div>"
            "<p><b>Группы:</b> {groups}</p>"
            "<p><b>Права (через группы):</b> {perms}</p>"
            "<p style='color:#888'>Редактирование прав отключено на форме пользователя. "
            "Назначайте права через группы.</p>"
            "</div>",
            groups=groups_str,
            perms=perms_html
        )
    permissions_summary.short_description = "Итоговый доступ"

    def get_readonly_fields(self, request, obj=None):
        """Добавляем резюме к readonly"""
        base = list(super().get_readonly_fields(request, obj))
        if 'permissions_summary' not in base:
            base.append('permissions_summary')
        return tuple(base)

    def get_list_display(self, request):
        """Добавляем телефон и группы в список пользователей"""
        base = list(super().get_list_display(request))
        # Добавляем после username, но перед email
        if 'username' in base:
            username_index = base.index('username')
            base.insert(username_index + 1, 'get_phone')
            base.insert(username_index + 2, 'get_user_groups')
        else:
            base.extend(['get_phone', 'get_user_groups'])
        return base

    def get_search_fields(self, request):
        """Добавляем поиск по телефону и группам"""
        base = list(super().get_search_fields(request))
        base.extend(['groups__name'])  # Поиск по названию групп
        return base

    def get_queryset(self, request):
        """Оптимизируем запросы для отображения телефонов и групп"""
        qs = super().get_queryset(request)
        qs = qs.prefetch_related('groups')  # Предзагружаем группы
        return qs

    def get_list_filter(self, request):
        """Добавляем фильтры по группам"""
        base = list(super().get_list_filter(request))
        base.append('groups')  # Фильтр по группам
        return base

    def get_fieldsets(self, request, obj=None):
        """Берем базовые fieldsets и фильтруем поля"""
        fieldsets = super().get_fieldsets(request, obj)
        new_fieldsets = []
        for name, opts in fieldsets:
            fields = list(opts.get('fields', ()))
            # Убираем управление правами/группами на форме
            fields = [f for f in fields if f not in ('groups', 'user_permissions')]
            # Оставляем is_superuser, is_staff, is_active видимыми
            if fields:
                new_fieldsets.append((name, {'fields': tuple(fields)}))

        # Добавим отдельный раздел "Доступ" с резюме
        new_fieldsets.append(('Доступ', {'fields': ('permissions_summary',)}))
        return tuple(new_fieldsets)

    def get_add_fieldsets(self, request):
        """Форма создания — тоже без прав/групп"""
        add_fieldsets = list(super().get_add_fieldsets(request))
        filtered = []
        for name, opts in add_fieldsets:
            fields = opts.get('fields', ())
            if isinstance(fields, (list, tuple)):
                fields = tuple(f for f in fields if f not in ('groups', 'user_permissions'))
            filtered.append((name, {'classes': opts.get('classes', ()), 'fields': fields}))
        return tuple(filtered)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('register/', Step1RegistrationView.as_view(), name='register_step1'),
            path('register/step2/<int:draft_id>/', Step2RegistrationView.as_view(), name='register_step2'),
            path('register/step3/<int:draft_id>/', Step3StaffRoleView.as_view(), name='register_step3_staff'),
            path('register/step3/profile/<int:draft_id>/', Step3ProfileView.as_view(), name='register_step3_profile'),
            path('register/step4/<int:draft_id>/', Step4ProfileView.as_view(), name='register_step4'),
            path('register/step4/relations/<int:draft_id>/', Step4RelationsView.as_view(), name='register_step4_relations'),
            path('register/cancel/', CancelRegistrationView.as_view(), name='register_cancel'),
            path('register/done/', DoneRegistrationView.as_view(), name='register_done'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Добавляем кнопку регистрации в список пользователей"""
        extra_context = extra_context or {}
        extra_context['show_registration_button'] = True
        return super().changelist_view(request, extra_context)
    
    def save_model(self, request, obj, form, change):
        """Синхронизируем ФИО из User в связанные профили"""
        super().save_model(request, obj, form, change)
        
        # Получаем ФИО из User
        user_first_name = obj.first_name
        user_last_name = obj.last_name
        
        # Синхронизируем с Athlete
        if hasattr(obj, 'athlete') and obj.athlete:
            athlete = obj.athlete
            if not athlete.first_name or not athlete.last_name:
                athlete.first_name = user_first_name
                athlete.last_name = user_last_name
                athlete.save(update_fields=['first_name', 'last_name'])
        
        # Синхронизируем с Trainer
        if hasattr(obj, 'trainer') and obj.trainer:
            trainer = obj.trainer
            if not trainer.first_name or not trainer.last_name:
                trainer.first_name = user_first_name
                trainer.last_name = user_last_name
                trainer.save(update_fields=['first_name', 'last_name'])
        
        # Синхронизируем с Parent
        if hasattr(obj, 'parent') and obj.parent:
            parent = obj.parent
            if not parent.first_name or not parent.last_name:
                parent.first_name = user_first_name
                parent.last_name = user_last_name
                parent.save(update_fields=['first_name', 'last_name'])
        
        # Синхронизируем с Staff
        if hasattr(obj, 'staff') and obj.staff:
            staff = obj.staff
            if not staff.first_name or not staff.last_name:
                staff.first_name = user_first_name
                staff.last_name = user_last_name
                staff.save(update_fields=['first_name', 'last_name'])

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


# ИСПРАВЛЕННЫЙ АДМИН ДЛЯ TRAININGGROUP
@admin.register(TrainingGroup)
class TrainingGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "trainer", "is_active")
    search_fields = ("name", "trainer__user__last_name", "trainer__user__first_name")
    fields = ("name", "trainer", "age_min", "age_max", "max_athletes", "is_active")
    autocomplete_fields = ['trainer']
    
    def get_form(self, request, obj=None, **kwargs):
        """Переопределяем для явного указания полей"""
        kwargs['fields'] = self.fields
        return super().get_form(request, obj, **kwargs)
    
    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path("create/", self.admin_site.admin_view(self.create_wizard_view), name="core_traininggroup_create_wizard"),
            path("create/step/<str:step>/", self.admin_site.admin_view(self.create_step_view), name="core_traininggroup_create_step"),
            path("<int:group_id>/panel/", self.admin_site.admin_view(self.panel_view), name="core_traininggroup_panel"),
            path("<int:group_id>/edit/", self.admin_site.admin_view(self.edit_group_view), name="core_traininggroup_edit"),
            path("<int:group_id>/children/", self.admin_site.admin_view(self.children_view), name="core_traininggroup_children"),
            path("<int:group_id>/schedule/", self.admin_site.admin_view(self.schedule_view), name="core_traininggroup_schedule"),
            path("<int:group_id>/journal/", self.admin_site.admin_view(self.journal_view), name="core_traininggroup_journal"),
        ]
        return extra + urls

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return redirect(reverse("admin:core_traininggroup_panel", args=[object_id]))
    
    def add_view(self, request, form_url="", extra_context=None):
        # Перенаправляем на мастер создания группы
        return redirect(reverse("admin:core_traininggroup_create_wizard"))
    
    def changelist_view(self, request, extra_context=None):
        """Переопределяем для добавления статистики"""
        # Получаем статистику
        total_groups = TrainingGroup.objects.count()
        active_groups = TrainingGroup.objects.filter(is_active=True).count()
        archived_groups = TrainingGroup.objects.filter(is_active=False).count()
        total_trainers = Trainer.objects.filter(is_archived=False).count()
        
        # Добавляем дополнительные данные для каждой группы
        from django.db.models import Count
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_groups': total_groups,
            'active_groups': active_groups,
            'archived_groups': archived_groups,
            'total_trainers': total_trainers,
            'trainers_list': Trainer.objects.filter(is_archived=False).select_related('user'),
        })
        
        response = super().changelist_view(request, extra_context)
        
        # Добавляем статистику к каждой группе в результатах
        if hasattr(response, 'context_data') and 'cl' in response.context_data:
            cl = response.context_data['cl']
            for group in cl.result_list:
                # Подсчеты для каждой группы
                group.children_count = AthleteTrainingGroup.objects.filter(training_group=group).count()
                group.schedule_count = GroupSchedule.objects.filter(training_group=group).count()
                group.sessions_count = TrainingSession.objects.filter(training_group=group).count()
        
        return response

    def panel_view(self, request, group_id: int):
        group = get_object_or_404(TrainingGroup, pk=group_id)
        if not self.has_view_permission(request, group):
            raise PermissionDenied

        children_count = AthleteTrainingGroup.objects.filter(training_group=group).count()
        schedule_count = GroupSchedule.objects.filter(training_group=group).count()
        today = timezone.localdate()
        next_session = (TrainingSession.objects
                        .filter(training_group=group, date__gte=today)
                        .order_by("date","start_time").first())

        # Получаем детей группы - принудительно выполняем запрос
        children = list(Athlete.objects
                       .filter(id__in=AthleteTrainingGroup.objects
                               .filter(training_group=group).values_list("athlete_id", flat=True))
                       .order_by("last_name","first_name"))

        # Получаем детальное расписание - принудительно выполняем запрос
        schedule_details = list(GroupSchedule.objects.filter(training_group=group).order_by('weekday'))

        ctx = {
            **self.admin_site.each_context(request),
            "title": f"Группа: {group.name}",
            "opts": self.model._meta,
            "group": group,
            "children": children,
            "schedule_details": schedule_details,
            "header": {
                "name": group.name,
                "trainer": str(getattr(group, "trainer", "—")),
                "children_count": children_count,
                "schedule_count": schedule_count,
                "next_session": next_session,
                "urls": {
                    "edit": reverse("admin:core_traininggroup_edit", args=[group.id]),
                    "children": reverse("admin:core_traininggroup_children", args=[group.id]),
                    "schedule": reverse("admin:core_traininggroup_schedule", args=[group.id]),
                    "journal": reverse("admin:core_traininggroup_journal", args=[group.id]),
                }
            }
        }
        return TemplateResponse(request, "admin/core/traininggroup/panel.html", ctx)

    def children_view(self, request, group_id):
        group = get_object_or_404(TrainingGroup, pk=group_id)
        if not self.has_view_permission(request, group):
            raise PermissionDenied

        members = (Athlete.objects
                   .filter(id__in=AthleteTrainingGroup.objects
                           .filter(training_group=group).values_list("athlete_id", flat=True))
                   .order_by("last_name","first_name"))

        # Доступные спортсмены (не в группе)
        available_athletes = (Athlete.objects
                             .exclude(id__in=AthleteTrainingGroup.objects
                                     .filter(training_group=group).values_list("athlete_id", flat=True))
                             .filter(is_archived=False)
                             .order_by("last_name","first_name"))

        if request.method == "POST":
            if not self.has_change_permission(request, group):
                raise PermissionDenied
            add_id = request.POST.get("athlete_id")
            rem_id = request.POST.get("remove_id")
            if add_id:
                AthleteTrainingGroup.objects.get_or_create(training_group=group, athlete_id=add_id)
                messages.success(request, "Ребёнок добавлен в группу.")
            if rem_id:
                AthleteTrainingGroup.objects.filter(training_group=group, athlete_id=rem_id).delete()
                messages.success(request, "Ребёнок убран из группы.")
            return redirect(request.path)

        ctx = {**self.admin_site.each_context(request),
               "title": f"Дети группы: {group.name}",
               "opts": self.model._meta, "group": group, "members": members, 
               "available_athletes": available_athletes}
        return TemplateResponse(request, "admin/core/traininggroup/children.html", ctx)

    def schedule_view(self, request, group_id):
        group = get_object_or_404(TrainingGroup, pk=group_id)
        if not self.has_view_permission(request, group):
            raise PermissionDenied

        current_schedule = GroupSchedule.objects.filter(training_group=group)
        current_weekdays = set(sch.weekday for sch in current_schedule)
        current_start_time = current_schedule.first().start_time if current_schedule.exists() else None
        current_end_time = current_schedule.first().end_time if current_schedule.exists() else None

        if request.method == "POST":
            if not self.has_change_permission(request, group):
                raise PermissionDenied
            
            weekdays = [int(d) for d in request.POST.getlist("weekdays") if d.isdigit()]
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            
            if weekdays and start_time and end_time:
                with transaction.atomic():
                    GroupSchedule.objects.filter(training_group=group).delete()
                    for weekday in weekdays:
                        GroupSchedule.objects.create(
                            training_group=group,
                            weekday=weekday,
                            start_time=start_time,
                            end_time=end_time
                        )
                    resync_future_sessions_for_group(group)
                    ensure_month_sessions_for_group(group)
                
                messages.success(request, "Расписание обновлено, будущие тренировки пересчитаны.")
                return redirect(request.path)
            else:
                messages.error(request, "Заполните все поля расписания.")

        # Превью дат текущего месяца
        today = timezone.localdate()
        first = today.replace(day=1)
        next_first = (first.replace(year=first.year+1, month=1, day=1)
                      if first.month==12 else first.replace(month=first.month+1, day=1))
        preview = []
        d = first
        while d < next_first:
            for weekday in current_weekdays:
                if d.weekday() == (weekday - 1):  # Преобразование 1-7 в 0-6
                    preview.append((d, current_start_time, current_end_time))
            d += timedelta(days=1)
        preview.sort()

        weekday_choices = [
            (1, 'Понедельник'), (2, 'Вторник'), (3, 'Среда'), (4, 'Четверг'),
            (5, 'Пятница'), (6, 'Суббота'), (7, 'Воскресенье')
        ]

        ctx = {
            **self.admin_site.each_context(request),
            "title": f"Расписание группы: {group.name}",
            "opts": self.model._meta,
            "group": group,
            "weekday_choices": weekday_choices,
            "current_weekdays": current_weekdays,
            "current_start_time": current_start_time,
            "current_end_time": current_end_time,
            "preview": preview,
        }
        return TemplateResponse(request, "admin/core/traininggroup/schedule.html", ctx)

    def journal_view(self, request, group_id):
        group = get_object_or_404(TrainingGroup, pk=group_id)
        if not self.has_view_permission(request, group):
            raise PermissionDenied

        ensure_month_sessions_for_group(group)
        
        today = timezone.localdate()
        
        if request.method == "POST":
            if not self.has_change_permission(request, group):
                raise PermissionDenied
            
            # Обработка AJAX запроса для изменения посещаемости
            if request.POST.get('action') == 'toggle_attendance':
                from django.http import JsonResponse
                import logging
                logger = logging.getLogger(__name__)
                
                try:
                    logger.info(f"Toggle attendance request: {request.POST}")
                    
                    session_id = int(request.POST.get('session_id'))
                    athlete_id = int(request.POST.get('athlete_id'))
                    is_present = request.POST.get('present') == 'true'
                    
                    logger.info(f"Parsed data: session_id={session_id}, athlete_id={athlete_id}, is_present={is_present}")
                    
                    session = get_object_or_404(TrainingSession, pk=session_id, training_group=group)
                    athlete = get_object_or_404(Athlete, pk=athlete_id)
                    
                    logger.info(f"Found session: {session}, athlete: {athlete}")
                    
                    # Проверяем, что сессия не закрыта и не в будущем
                    if session.is_closed:
                        return JsonResponse({'success': False, 'error': 'Сессия уже закрыта'})
                    
                    if session.date > today:
                        return JsonResponse({'success': False, 'error': 'Нельзя отмечать будущие тренировки'})
                    
                    # Получаем staff пользователя (если есть)
                    try:
                        marked_by_staff = request.user.staff
                    except:
                        # Если у пользователя нет профиля staff, ищем любого активного staff
                        marked_by_staff = Staff.objects.filter(user__is_active=True).first()
                    
                    logger.info(f"Marked by staff: {marked_by_staff}")
                    
                    # Получаем или создаем/удаляем запись посещаемости
                    attendance, created = AttendanceRecord.objects.get_or_create(
                        session=session,
                        athlete=athlete,
                        defaults={
                            'was_present': is_present,
                            'marked_by': marked_by_staff
                        }
                    )
                    
                    logger.info(f"Attendance record: {attendance}, created: {created}")
                    
                    if not created:
                        if is_present:
                            attendance.was_present = True
                            attendance.save()
                            logger.info("Updated attendance to present")
                        else:
                            attendance.delete()
                            logger.info("Deleted attendance record")
                    elif not is_present:
                        attendance.delete()
                        logger.info("Deleted newly created attendance record")
                    
                    return JsonResponse({'success': True, 'message': f'Посещаемость {"отмечена" if is_present else "убрана"}'})
                    
                except (ValueError, TrainingSession.DoesNotExist, Athlete.DoesNotExist) as e:
                    logger.error(f"Error in toggle_attendance: {e}")
                    return JsonResponse({'success': False, 'error': str(e)})
                except Exception as e:
                    logger.error(f"Unexpected error in toggle_attendance: {e}")
                    return JsonResponse({'success': False, 'error': f'Внутренняя ошибка сервера: {str(e)}'})
            
            # Обработка массового обновления посещаемости
            if request.POST.get('action') == 'bulk_update_attendance':
                from django.http import JsonResponse
                import json
                import logging
                logger = logging.getLogger(__name__)
                
                try:
                    changes_json = request.POST.get('changes')
                    changes = json.loads(changes_json)
                    
                    logger.info(f"Bulk update attendance: {len(changes)} changes")
                    
                    # Получаем staff пользователя
                    try:
                        marked_by_staff = request.user.staff
                    except:
                        marked_by_staff = Staff.objects.filter(user__is_active=True).first()
                    
                    updated_count = 0
                    
                    with transaction.atomic():
                        for change in changes:
                            session_id = int(change['session_id'])
                            athlete_id = int(change['athlete_id'])
                            is_present = change['present']
                            
                            session = get_object_or_404(TrainingSession, pk=session_id, training_group=group)
                            athlete = get_object_or_404(Athlete, pk=athlete_id)
                            
                            # Проверяем права на изменение
                            if session.is_closed or session.date > today:
                                continue  # Пропускаем недопустимые изменения
                            
                            # Обновляем или создаем/удаляем запись
                            attendance, created = AttendanceRecord.objects.get_or_create(
                                session=session,
                                athlete=athlete,
                                defaults={
                                    'was_present': is_present,
                                    'marked_by': marked_by_staff
                                }
                            )
                            
                            if not created:
                                if is_present:
                                    attendance.was_present = True
                                    attendance.save()
                                else:
                                    attendance.delete()
                            elif not is_present:
                                attendance.delete()
                            
                            updated_count += 1
                    
                    logger.info(f"Successfully updated {updated_count} attendance records")
                    return JsonResponse({'success': True, 'updated_count': updated_count})
                    
                except (ValueError, json.JSONDecodeError) as e:
                    logger.error(f"Error parsing bulk update data: {e}")
                    return JsonResponse({'success': False, 'error': 'Неверный формат данных'})
                except Exception as e:
                    logger.error(f"Unexpected error in bulk_update_attendance: {e}")
                    return JsonResponse({'success': False, 'error': f'Ошибка сервера: {str(e)}'})
            
            # Обработка закрытия сессии
            if request.POST.get('action') == 'close_session':
                today_session = TrainingSession.objects.filter(
                    training_group=group, date=today, is_closed=False
                ).first()
                
                if today_session:
                    today_session.is_closed = True
                    today_session.save(update_fields=["is_closed"])
                    messages.success(request, f"Сессия {today_session.date} закрыта.")
                else:
                    messages.error(request, "Сегодня нет активной тренировки для закрытия.")
                
                return redirect(request.path)

        # Находим сегодняшнюю активную сессию
        today_session = TrainingSession.objects.filter(
            training_group=group, date=today, is_closed=False
        ).first()

        # Все сессии текущего месяца
        first = today.replace(day=1)
        next_first = (first.replace(year=first.year+1, month=1, day=1)
                      if first.month==12 else first.replace(month=first.month+1, day=1))
        sessions = (TrainingSession.objects
                    .filter(training_group=group, date__gte=first, date__lt=next_first)
                    .order_by("date"))

        # Все дети группы
        children = (Athlete.objects
                    .filter(id__in=AthleteTrainingGroup.objects
                            .filter(training_group=group).values("athlete_id"))
                    .order_by("last_name","first_name"))

        # Записи посещаемости - только те, кто был отмечен как присутствующий
        present = {}
        for record in AttendanceRecord.objects.filter(session__in=sessions, was_present=True):
            if record.session_id not in present:
                present[record.session_id] = set()
            present[record.session_id].add(record.athlete_id)

        ctx = {
            **self.admin_site.each_context(request),
            "title": f"Журнал группы: {group.name}",
            "opts": self.model._meta,
            "group": group,
            "sessions": sessions,
            "children": children,
            "present": present,
            "today": today,
            "today_session": today_session,
        }
        return TemplateResponse(request, "admin/core/traininggroup/journal.html", ctx)

    def create_wizard_view(self, request):
        """Мастер создания группы - шаг 1: Данные группы"""
        if not self.has_add_permission(request):
            raise PermissionDenied

        if request.method == "POST":
            # Сохранение данных в сессию и переход к расписанию
            form_data = {
                'name': request.POST.get('name'),
                'trainer_id': request.POST.get('trainer'),
                'age_min': request.POST.get('age_min'),
                'age_max': request.POST.get('age_max'),
                'max_athletes': request.POST.get('max_athletes'),
                'is_active': bool(request.POST.get('is_active'))
            }
            
            # Проверяем обязательные поля
            if not form_data['name']:
                messages.error(request, "Название группы обязательно для заполнения.")
                # Возвращаемся на ту же страницу
                trainers = Trainer.objects.filter(is_archived=False).select_related('user')
                ctx = {
                    **self.admin_site.each_context(request),
                    "title": "Создать группу - Шаг 1: Данные группы",
                    "opts": self.model._meta,
                    "trainers": trainers,
                    "step": "data",
                    "next_step": "schedule",
                    "form_data": form_data  # Передаем данные обратно
                }
                return TemplateResponse(request, "admin/core/traininggroup/create_wizard.html", ctx)
            
            request.session['group_create_data'] = form_data
            messages.success(request, f"Данные группы '{form_data['name']}' сохранены. Переходим к расписанию.")
            return redirect(reverse("admin:core_traininggroup_create_step", args=["schedule"]))

        # GET запрос - показываем форму
        trainers = Trainer.objects.filter(is_archived=False).select_related('user')
        ctx = {
            **self.admin_site.each_context(request),
            "title": "Создать группу - Шаг 1: Данные группы",
            "opts": self.model._meta,
            "trainers": trainers,
            "step": "data",
            "next_step": "schedule"
        }
        return TemplateResponse(request, "admin/core/traininggroup/create_wizard.html", ctx)

    def create_step_view(self, request, step):
        """Шаги мастера создания группы"""
        if not self.has_add_permission(request):
            raise PermissionDenied

        group_data = request.session.get('group_create_data')
        if not group_data:
            messages.error(request, "Данные группы не найдены. Начните заново.")
            return redirect(reverse("admin:core_traininggroup_create_wizard"))

        if step == "schedule":
            return self._create_step_schedule(request, group_data)
        elif step == "children":
            return self._create_step_children(request, group_data)
        elif step == "finish":
            return self._create_step_finish(request, group_data)
        else:
            return redirect(reverse("admin:core_traininggroup_create_wizard"))

    def _create_step_schedule(self, request, group_data):
        """Шаг 2: Расписание группы"""
        if request.method == "POST":
            weekdays = [int(d) for d in request.POST.getlist("weekdays") if d.isdigit()]
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            
            if weekdays and start_time and end_time:
                # Создаем группу и расписание
                with transaction.atomic():
                    # Создаем группу
                    trainer = Trainer.objects.get(pk=group_data['trainer_id']) if group_data['trainer_id'] else None
                    group = TrainingGroup.objects.create(
                        name=group_data['name'],
                        trainer=trainer,
                        age_min=group_data['age_min'] or 0,
                        age_max=group_data['age_max'] or 100,
                        max_athletes=group_data['max_athletes'] or 20,
                        is_active=group_data['is_active']
                    )
                    
                    # Создаем расписание
                    for weekday in weekdays:
                        GroupSchedule.objects.create(
                            training_group=group,
                            weekday=weekday,
                            start_time=start_time,
                            end_time=end_time
                        )
                    
                    # Генерируем сессии
                    from .utils.sessions import ensure_month_sessions_for_group
                    ensure_month_sessions_for_group(group)
                    
                    # Очищаем сессию
                    if 'group_create_data' in request.session:
                        del request.session['group_create_data']
                    
                    messages.success(request, f"Группа '{group.name}' успешно создана с расписанием!")
                    return redirect(reverse("admin:core_traininggroup_changelist"))
            else:
                messages.error(request, "Заполните все поля расписания.")

        weekday_choices = [
            (1, 'Понедельник'), (2, 'Вторник'), (3, 'Среда'), (4, 'Четверг'),
            (5, 'Пятница'), (6, 'Суббота'), (7, 'Воскресенье')
        ]

        trainers = Trainer.objects.filter(is_archived=False).select_related('user')
        ctx = {
            **self.admin_site.each_context(request),
            "title": f"Создать группу - Шаг 2: Расписание для '{group_data['name']}'",
            "opts": self.model._meta,
            "group_data": group_data,
            "trainers": trainers,
            "weekday_choices": weekday_choices,
            "step": "schedule",
            "prev_step": "data"
        }
        return TemplateResponse(request, "admin/core/traininggroup/create_schedule.html", ctx)

    def edit_group_view(self, request, group_id):
        """Редактирование данных и расписания группы"""
        group = get_object_or_404(TrainingGroup, pk=group_id)
        if not self.has_change_permission(request, group):
            raise PermissionDenied

        if request.method == "POST":
            action = request.POST.get('action')
            
            if action == 'update_data':
                # Обновляем данные группы
                group.name = request.POST.get('name', group.name)
                trainer_id = request.POST.get('trainer')
                if trainer_id:
                    group.trainer = Trainer.objects.get(pk=trainer_id)
                else:
                    group.trainer = None
                group.age_min = int(request.POST.get('age_min', 0))
                group.age_max = int(request.POST.get('age_max', 100))
                group.max_athletes = int(request.POST.get('max_athletes', 20))
                group.is_active = bool(request.POST.get('is_active'))
                group.save()
                
                messages.success(request, "Данные группы обновлены.")
                
            elif action == 'update_schedule':
                # Обновляем расписание группы
                weekdays = [int(d) for d in request.POST.getlist("weekdays") if d.isdigit()]
                start_time = request.POST.get("start_time")
                end_time = request.POST.get("end_time")
                
                if weekdays and start_time and end_time:
                    with transaction.atomic():
                        # Удаляем старое расписание
                        GroupSchedule.objects.filter(training_group=group).delete()
                        # Создаем новое расписание
                        for weekday in weekdays:
                            GroupSchedule.objects.create(
                                training_group=group,
                                weekday=weekday,
                                start_time=start_time,
                                end_time=end_time
                            )
                        # Пересинхронизируем будущие сессии
                        from .utils.sessions import resync_future_sessions_for_group, ensure_month_sessions_for_group
                        resync_future_sessions_for_group(group)
                        ensure_month_sessions_for_group(group)
                    
                    messages.success(request, "Расписание обновлено, будущие тренировки пересчитаны.")
                else:
                    messages.error(request, "Заполните все поля расписания.")
            
            return redirect(reverse("admin:core_traininggroup_edit", args=[group.id]))

        # GET запрос - показываем форму
        trainers = Trainer.objects.filter(is_archived=False).select_related('user')
        current_schedule = GroupSchedule.objects.filter(training_group=group).order_by('weekday')
        current_weekdays = set(sch.weekday for sch in current_schedule)
        current_start_time = current_schedule.first().start_time if current_schedule.exists() else None
        current_end_time = current_schedule.first().end_time if current_schedule.exists() else None
        
        weekday_choices = [
            (1, 'Понедельник'), (2, 'Вторник'), (3, 'Среда'), (4, 'Четверг'),
            (5, 'Пятница'), (6, 'Суббота'), (7, 'Воскресенье')
        ]
        
        ctx = {
            **self.admin_site.each_context(request),
            "title": f"Редактировать группу: {group.name}",
            "opts": self.model._meta,
            "group": group,
            "trainers": trainers,
            "current_schedule": current_schedule,
            "current_weekdays": current_weekdays,
            "current_start_time": current_start_time,
            "current_end_time": current_end_time,
            "weekday_choices": weekday_choices,
        }
        return TemplateResponse(request, "admin/core/traininggroup/edit_group_tabs.html", ctx)

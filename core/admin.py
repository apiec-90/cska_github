from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Permission
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, reverse
from django.contrib import messages
from django.conf import settings
import os
import uuid
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
    TrainerRelationsForm
)
from .utils import assign_groups_for_registration

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
    list_display = ['get_full_name', 'get_phone', 'get_groups_count', 'get_athletes_count', 'get_active_status', 'is_archived']
    list_filter = ['is_archived', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'phone']
    ordering = ['user__last_name', 'user__first_name']
    # # убираем кастомный шаблон — оставляем стандартный вид
    # change_form_template = 'admin/core/trainer/change_form.html'

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
    
    def get_queryset(self, request):
        """Оптимизируем запросы"""
        qs = super().get_queryset(request)
        qs = qs.select_related('user').prefetch_related(
            'traininggroup_set'
        )
        return qs

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_role_display', 'get_phone', 'birth_date', 'get_active_status', 'is_archived']
    list_filter = ['role', 'is_archived', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'phone']
    ordering = ['user__last_name', 'user__first_name']
    # # используем стандартную форму
    # change_form_template = 'admin/core/staff/change_form.html'
    
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

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_phone', 'get_children_display', 'get_active_status', 'is_archived')
    list_filter = ('is_archived', 'user__is_active')
    search_fields = ('user__first_name', 'user__last_name', 'phone')
    ordering = ('user__last_name', 'user__first_name')
    # # убираем кастомный шаблон — оставляем стандартный вид
    # change_form_template = 'admin/core/parent/change_form.html'
    
    def get_full_name(self, obj):
        """Полное имя родителя"""
        first_name = (getattr(obj, 'first_name', None) or obj.user.first_name or "")
        last_name = (getattr(obj, 'last_name', None) or obj.user.last_name or "")
        return f"{last_name} {first_name}".strip() or obj.user.username
    get_full_name.short_description = "ФИО"
    
    def get_phone(self, obj):
        """Телефон родителя"""
        return obj.phone or "—"
    get_phone.short_description = "Телефон"
    
    def get_children_display(self, obj):
        """Дети родителя"""
        rels = obj.get_children_relations()

        if rels:
            children_names = []
            for rel in rels:
                child_name = f"{rel.athlete.user.last_name} {rel.athlete.user.first_name}".strip()
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

@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_phone', 'birth_date', 'get_groups_display', 'get_parents_display', 'get_active_status', 'is_archived')
    list_filter = ('is_archived', 'birth_date', 'user__is_active')
    search_fields = ('user__first_name', 'user__last_name', 'phone')
    ordering = ('user__last_name', 'user__first_name')
    # # инлайны не используем, карточка сверху формы
    inlines = []
    # # кастомный шаблон карточки спортсмена
    change_form_template = 'admin/core/athlete/change_form.html'

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
        first_name = (getattr(obj, 'first_name', None) or obj.user.first_name or "")
        last_name = (getattr(obj, 'last_name', None) or obj.user.last_name or "")
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
            role = form.cleaned_data['role']
            draft.role = role
            draft.current_step = 2
            draft.save()
            
            # Назначаем базовую группу по роли
            assign_groups_for_registration(draft.user, role)
            
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
            assign_groups_for_registration(draft.user, 'staff', subrole)
            
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
                    phone=form.cleaned_data.get('phone', '')
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
                    phone=form.cleaned_data.get('phone', '')
                )
                draft.current_step = 4
                draft.save()
                return HttpResponseRedirect(reverse('admin:register_step4_relations', args=[draft.id]))
        elif draft.role == 'trainer':
            form = TrainerForm(request.POST)
            if form.is_valid():
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

        if draft.role == 'trainer':
            form = TrainerForm()
        elif draft.role == 'parent':
            form = ParentForm()
        elif draft.role == 'athlete':
            form = AthleteForm()
        elif draft.role == 'staff':
            # На шаге 4 профиль без выбора роли/подроли
            from .forms import StaffRegisterProfileForm
            form = StaffRegisterProfileForm()
        else:
            messages.error(request, 'Неизвестная роль')
            return HttpResponseRedirect(reverse('admin:register_cancel'))

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

        if draft.role == 'trainer':
            form = TrainerForm(request.POST)
        elif draft.role == 'parent':
            form = ParentForm(request.POST)
        elif draft.role == 'athlete':
            form = AthleteForm(request.POST)
        elif draft.role == 'staff':
            from .forms import StaffRegisterProfileForm
            form = StaffRegisterProfileForm(request.POST)
        else:
            messages.error(request, 'Неизвестная роль')
            return HttpResponseRedirect(reverse('admin:register_cancel'))

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
                athlete = Athlete.objects.get(user=draft.user)
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
                parent = Parent.objects.get(user=draft.user)
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
                trainer = Trainer.objects.get(user=draft.user)
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

"""
Базовые классы для админок Django.
Устраняют дублирование кода между различными админками.
"""
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.utils.html import format_html
import os
import uuid
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

# Регистрируем стандартные Django модели
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class BasePersonAdmin(admin.ModelAdmin):
    """
    Базовый класс для админок пользователей (Trainer, Staff, Parent, Athlete).
    Содержит общие методы для работы с персональными данными.
    """
    
    # Общие поля для всех персональных админок
    readonly_fields = ['user']  # User только для чтения при редактировании
    exclude = ('user',)  # Убираем user из формы
    
    def get_full_name(self, obj):
        """Получить полное имя пользователя (универсальный метод)"""
        first_name = (getattr(obj, 'first_name', None) or obj.user.first_name or "")
        last_name = (getattr(obj, 'last_name', None) or obj.user.last_name or "")
        return f"{last_name} {first_name}".strip() or obj.user.username
    get_full_name.short_description = "ФИО"
    
    def get_phone(self, obj):
        """Получить телефон пользователя"""
        return getattr(obj, 'phone', None) or "—"
    get_phone.short_description = "Телефон"
    
    def get_active_status(self, obj):
        """Получить статус активности пользователя"""
        if obj.user.is_active:
            return "Активен"
        else:
            return "Неактивен"
    get_active_status.short_description = "Статус"
    
    def get_queryset(self, request):
        """Оптимизация запросов - предзагружаем связанного пользователя"""
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    def get_form(self, request, obj=None, **kwargs):
        """Инициализируем форму данными из User если поля пустые"""
        form = super().get_form(request, obj, **kwargs)
        
        if obj and obj.user_id:
            # Если поля профиля пустые, заполняем из User
            if not getattr(obj, 'first_name', None) and obj.user.first_name:
                obj.first_name = obj.user.first_name
            if not getattr(obj, 'last_name', None) and obj.user.last_name:
                obj.last_name = obj.user.last_name
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Синхронизируем ФИО между профилем и User"""
        super().save_model(request, obj, form, change)
        
        # Синхронизируем ФИО с User если поля есть в объекте
        if obj.user and hasattr(obj, 'first_name') and hasattr(obj, 'last_name'):
            user = obj.user
            user.first_name = obj.first_name or ""
            user.last_name = obj.last_name or ""
            user.save(update_fields=['first_name', 'last_name'])


class BaseDocumentMixin:
    """
    Миксин для админок с поддержкой документов и аватаров.
    Добавляет методы загрузки/удаления файлов.
    """
    
    def get_urls(self):
        """Добавляем URLs для загрузки документов"""
        from django.urls import path
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        custom_urls = [
            path('<path:object_id>/upload-avatar/', 
                 self.admin_site.admin_view(self.upload_avatar), 
                 name='%s_%s_upload_avatar' % info),
            path('<path:object_id>/upload-document/', 
                 self.admin_site.admin_view(self.upload_document), 
                 name='%s_%s_upload_document' % info),
            path('<path:object_id>/delete-document/', 
                 self.admin_site.admin_view(self.delete_document), 
                 name='%s_%s_delete_document' % info),
        ]
        return custom_urls + urls

    def upload_avatar(self, request, object_id):
        """Универсальная загрузка аватара"""
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        file_obj = request.FILES.get('avatar')
        if not file_obj:
            messages.error(request, 'Файл не выбран')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        try:
            obj = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            messages.error(request, f'{self.model._meta.verbose_name} не найден')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        # Проверяем формат файла
        file_extension = file_obj.name.split('.')[-1].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
        if file_extension not in allowed_extensions:
            messages.error(request, 'Недопустимый формат файла. Разрешены: JPG, PNG, GIF')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        try:
            # Создаем уникальное имя файла
            model_name = self.model._meta.model_name
            file_name = f"{model_name}_{obj.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
            
            # Сохраняем файл
            upload_path = os.path.join(settings.MEDIA_ROOT, 'avatars')
            os.makedirs(upload_path, exist_ok=True)
            
            file_path = os.path.join(upload_path, file_name)
            with open(file_path, 'wb') as f:
                for chunk in file_obj.chunks():
                    f.write(chunk)
            
            # Удаляем старые аватары
            self._delete_old_avatars(obj)
            
            # Создаем запись в Document
            self._create_avatar_document(obj, file_name, file_obj, request.user)
            
            messages.success(request, 'Аватар успешно загружен')
        except Exception as e:
            messages.error(request, f'Ошибка загрузки аватара: {e}')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
    
    def upload_document(self, request, object_id):
        """Универсальная загрузка документа"""
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        file_obj = request.FILES.get('document_file')
        comment = request.POST.get('comment', '')
        document_type_id = request.POST.get('document_type')
        
        if not file_obj:
            messages.error(request, 'Файл не выбран')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        try:
            obj = self.model.objects.get(pk=object_id)
            
            # Создаем уникальное имя файла
            model_name = self.model._meta.model_name
            file_extension = os.path.splitext(file_obj.name)[1]
            file_name = f"{model_name}_{obj.id}_doc_{uuid.uuid4().hex[:8]}{file_extension}"
            
            # Сохраняем файл
            upload_path = os.path.join(settings.MEDIA_ROOT, 'documents')
            os.makedirs(upload_path, exist_ok=True)
            
            file_path = os.path.join(upload_path, file_name)
            with open(file_path, 'wb') as f:
                for chunk in file_obj.chunks():
                    f.write(chunk)
            
            # Создаем запись в Document
            self._create_document_record(obj, file_name, file_obj, comment, document_type_id, request.user)
            
            messages.success(request, 'Документ успешно загружен')
        except Exception as e:
            messages.error(request, f'Ошибка загрузки документа: {e}')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
    
    def delete_document(self, request, object_id):
        """Универсальное удаление документа"""
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        document_id = request.POST.get('document_id')
        if not document_id:
            messages.error(request, 'ID документа не указан')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        try:
            from core.models import Document
            document = Document.objects.get(pk=document_id)
            
            # Удаляем физический файл
            self._delete_physical_file(document.file)
            
            # Удаляем запись из БД
            document.delete()
            messages.success(request, 'Документ успешно удален')
        except Exception as e:
            messages.error(request, f'Ошибка удаления документа: {e}')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
    
    def _delete_old_avatars(self, obj):
        """Удалить старые аватары объекта"""
        from core.models import Document, DocumentType
        try:
            avatar_type = DocumentType.objects.get(name='Аватар')
            ct = ContentType.objects.get_for_model(self.model)
            old_avatars = Document.objects.filter(
                content_type=ct, 
                object_id=obj.id, 
                document_type=avatar_type
            )
            for avatar in old_avatars:
                self._delete_physical_file(avatar.file)
                avatar.delete()
        except Exception:
            pass  # Не критично если не удалось
    
    def _create_avatar_document(self, obj, file_name, file_obj, user):
        """Создать запись Document для аватара"""
        from core.models import Document, DocumentType
        
        avatar_type, _ = DocumentType.objects.get_or_create(name='Аватар')
        ct = ContentType.objects.get_for_model(self.model)
        
        Document.objects.create(
            document_type=avatar_type,
            content_type=ct,
            object_id=obj.id,
            file=f'avatars/{file_name}',
            file_type=file_obj.content_type,
            file_size=file_obj.size,
            uploaded_by=user,
            comment='Загружен как аватар'
        )
    
    def _create_document_record(self, obj, file_name, file_obj, comment, document_type_id, user):
        """Создать запись Document для документа"""
        from core.models import Document, DocumentType
        
        # Получаем или создаем тип документа
        if document_type_id:
            try:
                doc_type = DocumentType.objects.get(pk=document_type_id)
            except DocumentType.DoesNotExist:
                doc_type, _ = DocumentType.objects.get_or_create(name='Прочее')
        else:
            doc_type, _ = DocumentType.objects.get_or_create(name='Прочее')
        
        ct = ContentType.objects.get_for_model(self.model)
        
        Document.objects.create(
            document_type=doc_type,
            content_type=ct,
            object_id=obj.id,
            file=f'documents/{file_name}',
            file_type=file_obj.content_type,
            file_size=file_obj.size,
            uploaded_by=user,
            comment=comment
        )
    
    def _delete_physical_file(self, file_path):
        """Удалить физический файл"""
        try:
            # Обрабатываем различные форматы путей
            file_url = str(file_path)
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            
            if file_url.startswith(media_url):
                rel_path = file_url[len(media_url):]
            elif '/media/' in file_url:
                rel_path = file_url.split('/media/', 1)[1]
            else:
                rel_path = file_url.lstrip('/')
            
            full_path = os.path.join(media_root, rel_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception:
            pass  # Не критично если файл не удалось удалить


class BaseChangeFormMixin:
    """
    Миксин для расширения changeform_view с дополнительными данными.
    Добавляет общую логику для показа документов в формах редактирования.
    """
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Добавляем документы и типы документов в контекст"""
        extra_context = extra_context or {}
        documents = []
        doc_types = []
        avatar_url = None
        
        if object_id:
            try:
                from core.models import Document, DocumentType
                
                obj = self.model.objects.get(pk=object_id)
                doc_types = DocumentType.objects.all().order_by('name')
                
                # Получаем документы объекта
                ct = ContentType.objects.get_for_model(self.model)
                documents = Document.objects.filter(
                    content_type=ct,
                    object_id=obj.id
                ).select_related('document_type', 'uploaded_by').order_by('-uploaded_at')
                
                # Ищем аватар
                try:
                    avatar_type = DocumentType.objects.get(name='Аватар')
                    avatar_doc = documents.filter(document_type=avatar_type).first()
                    if avatar_doc:
                        avatar_url = avatar_doc.file
                except DocumentType.DoesNotExist:
                    pass
                
            except self.model.DoesNotExist:
                pass
        
        # Добавляем данные в контекст с префиксом модели
        model_name = self.model._meta.model_name
        extra_context.update({
            f'{model_name}_documents': documents,
            f'{model_name}_document_types': doc_types,
            f'{model_name}_avatar_url': avatar_url,
        })
        
        return super().changeform_view(request, object_id, form_url, extra_context)


# Инлайны для связей пользователей
class AthleteParentInline(admin.TabularInline):
    """Inline для управления родителями спортсмена"""
    from core.models import AthleteParent
    model = AthleteParent
    fk_name = 'athlete'
    extra = 1
    verbose_name = "Родитель"
    verbose_name_plural = "Родители"


class AthleteTrainingGroupInline(admin.TabularInline):
    """Inline для управления группами спортсмена"""
    from core.models import AthleteTrainingGroup
    model = AthleteTrainingGroup
    fk_name = 'athlete'
    extra = 0
    verbose_name = "Тренировочная группа"
    verbose_name_plural = "Тренировочные группы"
    fields = ('training_group',)
    autocomplete_fields = ['training_group']


class ParentAthleteInline(admin.TabularInline):
    """Inline для управления детьми родителя"""
    from core.models import AthleteParent
    model = AthleteParent
    fk_name = 'parent'
    extra = 1
    verbose_name = "Ребенок"
    verbose_name_plural = "Дети"
    fields = ('athlete',)
    autocomplete_fields = ['athlete']
"""
Base classes for Django admin interfaces.
Eliminate code duplication between different admin interfaces.
"""
from typing import Any, Optional, List
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.utils.html import format_html
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.urls import URLPattern, path
import os
import uuid
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Create custom User admin with additional URLs for registration
class UserRoleListFilter(admin.SimpleListFilter):
    """Custom filter for user roles in admin"""
    title = 'роль пользователя'
    parameter_name = 'user_role'
    
    def lookups(self, request, model_admin):
        return (
            ('athlete', '🏃 Спортсмен'),
            ('parent', '👨‍👩‍👧‍👦 Родитель'),
            ('trainer', '🏋️ Тренер'),
            ('staff', '💼 Сотрудник'),
            ('admin', '🔑 Администратор'),
            ('undefined', '❓ Не определено'),
        )
    
    def queryset(self, request, queryset):
        from core.models import Athlete, Parent, Trainer, Staff
        
        if self.value() == 'athlete':
            return queryset.filter(athlete__isnull=False)
        elif self.value() == 'parent':
            return queryset.filter(parent__isnull=False)
        elif self.value() == 'trainer':
            return queryset.filter(trainer__isnull=False)
        elif self.value() == 'staff':
            return queryset.filter(staff__isnull=False)
        elif self.value() == 'admin':
            return queryset.filter(is_superuser=True)
        elif self.value() == 'undefined':
            return queryset.filter(
                athlete__isnull=True,
                parent__isnull=True,
                trainer__isnull=True,
                staff__isnull=True,
                is_superuser=False
            )
        return queryset


class CustomUserAdmin(UserAdmin):
    """Extend standard UserAdmin to add registration URLs and role display"""
    
    # Add role column to the user list display
    list_display = UserAdmin.list_display + ('get_user_role', 'get_groups_display')
    
    # Add custom filters
    list_filter = UserAdmin.list_filter + (UserRoleListFilter,)
    
    def get_queryset(self, request):
        """Optimize queryset to prevent N+1 queries"""
        qs = super().get_queryset(request)
        return qs.select_related('athlete', 'parent', 'trainer', 'staff').prefetch_related('groups')
    
    def get_user_role(self, obj: User) -> str:
        """Get user's role based on their profile"""
        from core.models import Athlete, Parent, Trainer, Staff
        
        try:
            if hasattr(obj, 'athlete') or Athlete.objects.filter(user=obj).exists():
                return "🏃 Спортсмен"
            elif hasattr(obj, 'parent') or Parent.objects.filter(user=obj).exists():
                return "👨‍👩‍👧‍👦 Родитель"
            elif hasattr(obj, 'trainer') or Trainer.objects.filter(user=obj).exists():
                return "🏋️ Тренер"
            elif hasattr(obj, 'staff') or Staff.objects.filter(user=obj).exists():
                staff = Staff.objects.filter(user=obj).first()
                if staff:
                    return f"💼 {staff.get_role_display()}"
                return "💼 Сотрудник"
            elif obj.is_superuser:
                return "🔑 Администратор"
            else:
                return "❓ Не определено"
        except Exception:
            return "❓ Ошибка"
    
    get_user_role.short_description = "Роль"
    get_user_role.admin_order_field = 'username'
    
    def get_groups_display(self, obj: User) -> str:
        """Display user's Django groups"""
        groups = obj.groups.all()
        if groups:
            return ", ".join([group.name for group in groups])
        return "—"
    
    get_groups_display.short_description = "Группы"
    
    def get_urls(self) -> List[URLPattern]:
        """Add URLs for user registration"""
        urls = super().get_urls()
        from core.admin_registration import (
            Step1RegistrationView, Step2RegistrationView, Step3RegistrationView,
            register_done_view, register_cancel_view
        )
        
        custom_urls = [
            path('register/', Step1RegistrationView.as_view(), name='register_step1'),
            path('register/step2/<int:draft_id>/', Step2RegistrationView.as_view(), name='register_step2'),
            path('register/step3/<int:draft_id>/', Step3RegistrationView.as_view(), name='register_step3'),
            path('register/done/', register_done_view, name='register_done'),
            path('register/cancel/', register_cancel_view, name='register_cancel'),
        ]
        return custom_urls + urls

# Register our custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class BasePersonAdmin(admin.ModelAdmin):
    """
    Base class for user admin interfaces (Trainer, Staff, Parent, Athlete).
    Contains common methods for working with personal data.
    """
    
    # Common fields for all personal admin interfaces
    readonly_fields = ['user']  # User is read-only when editing
    exclude = ('user',)  # Remove user from form
    
    def get_full_name(self, obj: Any) -> str:
        """Get user's full name (universal method)"""
        first_name = (getattr(obj, 'first_name', None) or obj.user.first_name or "")
        last_name = (getattr(obj, 'last_name', None) or obj.user.last_name or "")
        return f"{last_name} {first_name}".strip() or obj.user.username
    get_full_name.short_description = "Full Name"
    
    def get_phone(self, obj: Any) -> str:
        """Get user's phone number"""
        return getattr(obj, 'phone', None) or "—"
    get_phone.short_description = "Phone"
    
    def get_active_status(self, obj: Any) -> str:
        """Get user's activity status"""
        if obj.user.is_active:
            return "Active"
        else:
            return "Inactive"
    get_active_status.short_description = "Status"
    
    def get_queryset(self, request: HttpRequest) -> models.QuerySet:
        """Optimize queries - preload related user"""
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    def get_form(self, request: HttpRequest, obj: Optional[Any] = None, change: bool = False, **kwargs: Any) -> Any:
        """Initialize form with User data if profile fields are empty"""
        form = super().get_form(request, obj, change=change, **kwargs)
        
        if obj and obj.user_id:
            # If profile fields are empty, fill from User
            if not getattr(obj, 'first_name', None) and obj.user.first_name:
                obj.first_name = obj.user.first_name
            if not getattr(obj, 'last_name', None) and obj.user.last_name:
                obj.last_name = obj.user.last_name
        
        return form
    
    def save_model(self, request: HttpRequest, obj: Any, form: Any, change: bool) -> None:
        """Synchronize names between profile and User"""
        super().save_model(request, obj, form, change)
        
        # Sync names with User if fields exist in object
        if obj.user and hasattr(obj, 'first_name') and hasattr(obj, 'last_name'):
            user = obj.user
            user.first_name = obj.first_name or ""
            user.last_name = obj.last_name or ""
            user.save(update_fields=['first_name', 'last_name'])


class BaseDocumentMixin:
    """
    Mixin for admin interfaces with document and avatar support.
    Adds file upload/deletion methods.
    """
    
    def get_urls(self) -> List[URLPattern]:
        """Add URLs for document uploads"""
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

    def upload_avatar(self, request: HttpRequest, object_id: str) -> HttpResponse:
        """Universal avatar upload"""
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        # ... existing code ...
        
        file_obj = request.FILES.get('avatar')
        if not file_obj:
            messages.error(request, 'File not selected')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        try:
            obj = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            messages.error(request, f'{self.model._meta.verbose_name} not found')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        # Check file format
        file_extension = file_obj.name.split('.')[-1].lower()
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
        if file_extension not in allowed_extensions:
            messages.error(request, 'Invalid file format. Allowed: JPG, PNG, GIF')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        try:
            # Create unique filename
            model_name = self.model._meta.model_name
            file_name = f"{model_name}_{obj.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
            
            # Read file data
            file_data = b''
            for chunk in file_obj.chunks():
                file_data += chunk
            
            # Try to upload to Supabase Storage first
            from core.utils.supabase_storage import upload_to_supabase_storage
            supabase_path = f"avatars/{file_name}"
            success, result = upload_to_supabase_storage(file_data, supabase_path)
            
            if success:
                # Supabase upload successful
                messages.success(request, f'Avatar uploaded to Supabase Storage: {file_name}')
                supabase_url = result
            else:
                # Fallback to local storage
                upload_path = os.path.join(settings.MEDIA_ROOT, 'avatars')
                os.makedirs(upload_path, exist_ok=True)
                
                file_path = os.path.join(upload_path, file_name)
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                messages.warning(request, f'Avatar saved locally (Supabase error: {result})')
                supabase_url = None
            
            # Delete old avatars (both local and Supabase)
            self._delete_old_avatars(obj)
            
            # Create Document record with Supabase URL if available
            self._create_avatar_document(obj, file_name, file_obj, request.user, supabase_url)
            
            messages.success(request, 'Avatar uploaded successfully')
            
            # Для AJAX запросов возвращаем JSON
            if request.headers.get('Content-Type', '').startswith('multipart/form-data'):
                from django.http import JsonResponse
                return JsonResponse({'success': True, 'message': 'Avatar uploaded successfully'})
                
        except Exception as e:
            messages.error(request, f'Avatar upload error: {e}')
            
            # Для AJAX запросов возвращаем JSON с ошибкой
            if request.headers.get('Content-Type', '').startswith('multipart/form-data'):
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'error': str(e)})
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
    
    def upload_document(self, request: HttpRequest, object_id: str) -> HttpResponse:
        """Universal document upload"""
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
            
            # Read file data
            file_data = b''
            for chunk in file_obj.chunks():
                file_data += chunk
            
            # Try to upload to Supabase Storage first
            from core.utils.supabase_storage import upload_to_supabase_storage
            supabase_path = f"documents/{file_name}"
            success, result = upload_to_supabase_storage(file_data, supabase_path)
            
            if success:
                # Supabase upload successful
                messages.success(request, f'Document uploaded to Supabase Storage: {file_name}')
                supabase_url = result
                file_storage_path = supabase_url
            else:
                # Fallback to local storage
                upload_path = os.path.join(settings.MEDIA_ROOT, 'documents')
                os.makedirs(upload_path, exist_ok=True)
                
                file_path = os.path.join(upload_path, file_name)
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                messages.warning(request, f'Document saved locally (Supabase error: {result})')
                file_storage_path = f'documents/{file_name}'
            
            # Создаем запись в Document с правильным путем
            self._create_document_record(obj, file_name, file_obj, comment, document_type_id, request.user, file_storage_path)
            
            messages.success(request, 'Документ успешно загружен')
            
            # Для AJAX запросов возвращаем JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                from django.http import JsonResponse
                # Return appropriate URL based on storage location
                if success:
                    file_url = supabase_url
                else:
                    file_url = f'/media/documents/{file_name}'
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Документ успешно загружен',
                    'file_url': file_url,
                    'file_name': file_name
                })
                
        except Exception as e:
            messages.error(request, f'Ошибка загрузки документа: {e}')
            
            # Для AJAX запросов возвращаем JSON с ошибкой
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'error': str(e)})
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
    
    def delete_document(self, request: HttpRequest, object_id: str) -> HttpResponse:
        """Universal document deletion"""
        if request.method != 'POST':
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        document_id = request.POST.get('document_id')
        if not document_id:
            messages.error(request, 'Document ID not specified')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        try:
            from core.models import Document
            document = Document.objects.get(pk=document_id)
            
            # Delete physical file
            self._delete_physical_file(document.file)
            
            # Delete database record
            document.delete()
            messages.success(request, 'Document deleted successfully')
        except Exception as e:
            messages.error(request, f'Document deletion error: {e}')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
    
    def _delete_old_avatars(self, obj: Any) -> None:
        """Delete old object avatars (both local and Supabase)"""
        from core.models import Document, DocumentType
        try:
            avatar_type = DocumentType.objects.get(name='Avatar')
            ct = ContentType.objects.get_for_model(self.model)
            old_avatars = Document.objects.filter(
                content_type=ct, 
                object_id=obj.id, 
                document_type=avatar_type
            )
            for avatar in old_avatars:
                # Try to delete from Supabase Storage if it's a Supabase URL
                if avatar.file.startswith('http') and 'supabase' in avatar.file:
                    # Extract file path from Supabase URL
                    # URL format: https://xxx.supabase.co/storage/v1/object/public/media/avatars/filename.jpg
                    try:
                        path_parts = avatar.file.split('/storage/v1/object/public/media/')
                        if len(path_parts) > 1:
                            file_path = path_parts[1]
                            from core.utils.supabase_storage import delete_from_supabase_storage
                            delete_from_supabase_storage(file_path)
                    except Exception:
                        pass
                else:
                    # Delete local file
                    self._delete_physical_file(avatar.file)
                
                avatar.delete()
        except Exception:
            pass  # Not critical if deletion fails
    
    def _create_avatar_document(self, obj: Any, file_name: str, file_obj: Any, user: Any, supabase_url: str = None) -> None:
        """Create Document record for avatar"""
        from core.models import Document, DocumentType
        
        avatar_type, _ = DocumentType.objects.get_or_create(name='Avatar')
        ct = ContentType.objects.get_for_model(self.model)
        
        # Use Supabase URL if available, otherwise use local path
        file_path = supabase_url if supabase_url else f'avatars/{file_name}'
        comment = 'Uploaded to Supabase Storage' if supabase_url else 'Uploaded locally'
        
        Document.objects.create(
            document_type=avatar_type,
            content_type=ct,
            object_id=obj.id,
            file=file_path,
            file_type=file_obj.content_type,
            file_size=file_obj.size,
            uploaded_by=user,
            comment=comment
        )
    
    def _create_document_record(self, obj: Any, file_name: str, file_obj: Any, comment: str, document_type_id: str, user: Any, file_path: str = None) -> None:
        """Create Document record for document"""
        from core.models import Document, DocumentType
        
        # Get or create document type
        if document_type_id:
            try:
                doc_type = DocumentType.objects.get(pk=document_type_id)
            except DocumentType.DoesNotExist:
                doc_type, _ = DocumentType.objects.get_or_create(name='Other')
        else:
            doc_type, _ = DocumentType.objects.get_or_create(name='Other')
        
        ct = ContentType.objects.get_for_model(self.model)
        
        # Use provided file_path or fallback to local path
        storage_path = file_path if file_path else f'documents/{file_name}'
        storage_comment = comment
        
        # Add storage info to comment
        if file_path and 'supabase' in file_path.lower():
            storage_comment = f"{comment} (Uploaded to Supabase Storage)" if comment else "Uploaded to Supabase Storage"
        
        Document.objects.create(
            document_type=doc_type,
            content_type=ct,
            object_id=obj.id,
            file=storage_path,
            file_type=file_obj.content_type,
            file_size=file_obj.size,
            uploaded_by=user,
            comment=storage_comment
        )
    
    def _delete_physical_file(self, file_path: str) -> None:
        """Delete physical file (both local and Supabase)"""
        try:
            file_url = str(file_path)
            
            # Check if it's a Supabase Storage URL
            if 'supabase' in file_url.lower() and '/storage/v1/object/public/' in file_url:
                try:
                    # Extract file path from Supabase URL
                    # Format: https://xxx.supabase.co/storage/v1/object/public/media/documents/filename
                    path_parts = file_url.split('/storage/v1/object/public/media/')
                    if len(path_parts) > 1:
                        supabase_file_path = path_parts[1]
                        from core.utils.supabase_storage import delete_from_supabase_storage
                        success, result = delete_from_supabase_storage(supabase_file_path)
                        if not success:
                            logger.warning(f"Failed to delete from Supabase: {result}")
                except Exception as e:
                    logger.warning(f"Supabase deletion error: {e}")
            else:
                # Handle local file deletion
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
        except Exception as e:
            logger.warning(f"File deletion error: {e}")  # Log but don't fail


class BaseChangeFormMixin:
    """
    Mixin for extending changeform_view with additional data.
    Adds common logic for showing documents in edit forms.
    """
    
    def changeform_view(
        self, 
        request: HttpRequest, 
        object_id: Optional[str] = None, 
        form_url: str = '', 
        extra_context: Optional[dict[str, Any]] = None
    ) -> HttpResponse:
        """Add documents and document types to context"""
        extra_context = extra_context or {}
        documents = []
        doc_types = []
        avatar_url = None
        
        if object_id:
            try:
                from core.models import Document, DocumentType
                
                obj = self.model.objects.get(pk=object_id)
                doc_types = DocumentType.objects.all().order_by('name')
                
                # Get object documents
                ct = ContentType.objects.get_for_model(self.model)
                documents = Document.objects.filter(
                    content_type=ct,
                    object_id=obj.id
                ).select_related('document_type', 'uploaded_by').order_by('-uploaded_at')
                
                # Look for avatar
                try:
                    avatar_type = DocumentType.objects.get(name='Avatar')
                    avatar_doc = documents.filter(document_type=avatar_type).first()
                    if avatar_doc:
                        media_url = getattr(settings, 'MEDIA_URL', '/media/')
                        avatar_url = f"{media_url}{avatar_doc.file}"
                except DocumentType.DoesNotExist:
                    pass
                
            except self.model.DoesNotExist:
                pass
        
        # Add data to context with model prefix
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
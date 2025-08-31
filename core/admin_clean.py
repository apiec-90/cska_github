# Импорт админок из модулей для лучшей организации кода
from .admin import *

# Остальной код admin.py временно перемещен в модули
# Здесь остаются только URL patterns для регистрации пользователей

from django.views import View
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from core.models import RegistrationDraft
from core.forms import Step1UserForm, Step2RoleForm
from core import utils


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
            
            messages.success(request, f'Роль {role} выбрана. Переходим к следующему шагу.')
            # Временно редиректим на завершение
            return HttpResponseRedirect(reverse('admin:register_done'))
        
        return render(request, 'admin/core/registration/step2.html', {
            'form': form,
            'draft': draft,
            'title': 'Шаг 2 - Выбор роли',
            'opts': User._meta,
        })

# Добавляем URL patterns для регистрации к существующим админкам
from django.urls import path

# Для добавления URL patterns к админке пользователей
def get_registration_urls():
    """Возвращает URL patterns для процесса регистрации"""
    return [
        path('register/', Step1RegistrationView.as_view(), name='register_step1'),
        path('register/step2/<int:draft_id>/', Step2RegistrationView.as_view(), name='register_step2'),
        path('register/done/', lambda request: render(request, 'admin/core/registration/done.html'), name='register_done'),
    ]


# Note: TrainerAdmin, ParentAdmin, AthleteAdmin are now handled by core.admin.user_admins module
# to avoid duplicate registrations which were causing URL resolution errors

# All other admin classes continue below from the original file...
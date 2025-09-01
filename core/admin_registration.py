"""
Django Admin registration views for multi-step user registration.
Contains views for creating users through the admin interface.
"""
from typing import Any, Optional
from django.views import View
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from core.models import RegistrationDraft
from core.forms import Step1UserForm, Step2RoleForm
from core import utils


class RegistrationAdminView(View):
    """Base class for admin registration views"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)


class Step1RegistrationView(RegistrationAdminView):
    """Step 1: Create temporary user"""
    
    def get(self, request: HttpRequest) -> HttpResponse:
        # Clean up existing draft
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
            'title': 'Step 1 - Create User',
            'opts': User._meta,
        })
    
    def post(self, request: HttpRequest) -> HttpResponse:
        form = Step1UserForm(request.POST)
        if form.is_valid():
            # Create temporary user
            user = form.save(commit=False)
            user.is_active = False  # Temporarily inactive
            user.save()
            
            # Create registration draft
            draft = RegistrationDraft.objects.create(
                user=user,
                created_by=request.user,
                current_step=1
            )
            
            request.session['draft_id'] = draft.id
            print(f"Created draft #{draft.id} for user {user.username}")
            messages.success(request, f'User {user.username} created. Proceeding to role selection.')
            
            return HttpResponseRedirect(reverse('admin:register_step2', args=[draft.id]))
        
        return render(request, 'admin/core/registration/step1.html', {
            'form': form,
            'title': 'Step 1 - Create User',
            'opts': User._meta,
        })


class Step2RegistrationView(RegistrationAdminView):
    """Step 2: Role selection"""
    
    def get(self, request: HttpRequest, draft_id: int) -> HttpResponse:
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Draft #{draft_id} not found or already completed.')
            return HttpResponseRedirect(reverse('admin:register_step1'))
        
        form = Step2RoleForm(initial={'role': draft.role})
        
        return render(request, 'admin/core/registration/step2.html', {
            'form': form,
            'draft': draft,
            'title': 'Step 2 - Role Selection',
            'opts': User._meta,
        })
    
    def post(self, request: HttpRequest, draft_id: int) -> HttpResponse:
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Draft #{draft_id} not found or already completed.')
            return HttpResponseRedirect(reverse('admin:register_step1'))
        
        form = Step2RoleForm(request.POST)
        
        if form.is_valid():
            role = form.cleaned_data['role']
            draft.role = role
            draft.current_step = 2
            draft.save()
            
            # Assign basic groups by role
            utils.assign_groups_for_registration(draft.user, role)
            
            messages.success(request, f'Role {role} selected. Proceeding to profile details.')
            return HttpResponseRedirect(reverse('admin:register_step3', args=[draft.id]))
        
        return render(request, 'admin/core/registration/step2.html', {
            'form': form,
            'draft': draft,
            'title': 'Step 2 - Role Selection',
            'opts': User._meta,
        })
    
    def _create_profile_for_role(self, user: User, role: str, form_data: Optional[dict] = None) -> None:
        """Create the appropriate profile record based on the user's role"""
        from core.models import Athlete, Parent, Trainer, Staff
        from datetime import date
        
        # Get names from User object or form data
        if form_data:
            first_name = form_data.get('first_name', user.first_name or '')
            last_name = form_data.get('last_name', user.last_name or '')
            phone = form_data.get('phone', '+7 (999) 000-00-00')
            birth_date = form_data.get('birth_date', date(2000, 1, 1))
        else:
            first_name = user.first_name or ''
            last_name = user.last_name or ''
            phone = '+7 (999) 000-00-00'
            birth_date = date(2000, 1, 1)
        
        try:
            if role == 'athlete':
                Athlete.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'birth_date': birth_date,
                        'phone': phone,
                    }
                )
            elif role == 'parent':
                Parent.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'birth_date': birth_date,
                        'phone': phone,
                    }
                )
            elif role == 'trainer':
                Trainer.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'birth_date': birth_date,
                        'phone': phone,
                    }
                )
            elif role == 'staff':
                Staff.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'birth_date': birth_date,
                        'phone': phone,
                        'role': 'manager',  # Default staff role
                    }
                )
            print(f"✅ Created {role} profile for user {user.username}")
        except Exception as e:
            print(f"❌ Error creating profile for {user.username} with role {role}: {e}")


class Step3RegistrationView(RegistrationAdminView):
    """Step 3: Profile details"""
    
    def get(self, request: HttpRequest, draft_id: int) -> HttpResponse:
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Draft #{draft_id} not found or already completed.')
            return HttpResponseRedirect(reverse('admin:register_step1'))
        
        if not draft.role:
            messages.error(request, 'Role not selected. Please complete step 2 first.')
            return HttpResponseRedirect(reverse('admin:register_step2', args=[draft_id]))
        
        from core.forms import CommonProfileForm
        form = CommonProfileForm(initial={
            'first_name': draft.user.first_name,
            'last_name': draft.user.last_name,
        })
        
        return render(request, 'admin/core/registration/step3.html', {
            'form': form,
            'draft': draft,
            'title': 'Step 3 - Profile Details',
            'opts': User._meta,
        })
    
    def post(self, request: HttpRequest, draft_id: int) -> HttpResponse:
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
        except RegistrationDraft.DoesNotExist:
            messages.error(request, f'Draft #{draft_id} not found or already completed.')
            return HttpResponseRedirect(reverse('admin:register_step1'))
        
        from core.forms import CommonProfileForm
        form = CommonProfileForm(request.POST)
        
        if form.is_valid():
            # Save name data to User
            draft.user.first_name = form.cleaned_data['first_name']
            draft.user.last_name = form.cleaned_data['last_name']
            draft.user.save()
            
            # Create the profile record based on role
            self._create_profile_for_role(draft.user, draft.role, form.cleaned_data)
            
            # Activate user and complete registration
            draft.user.is_active = True
            draft.user.save()
            draft.current_step = 3
            draft.is_completed = True
            draft.save()
            request.session.pop('draft_id', None)
            
            messages.success(request, f'User {draft.user.username} registered successfully with profile!')
            return HttpResponseRedirect(reverse('admin:register_done'))
        
        return render(request, 'admin/core/registration/step3.html', {
            'form': form,
            'draft': draft,
            'title': 'Step 3 - Profile Details',
            'opts': User._meta,
        })
    
    def _create_profile_for_role(self, user: User, role: str, form_data: dict) -> None:
        """Create the appropriate profile record based on the user's role"""
        from core.models import Athlete, Parent, Trainer, Staff
        
        # Get data from form
        first_name = form_data.get('first_name', '')
        last_name = form_data.get('last_name', '')
        phone = form_data.get('phone', '+7 (999) 000-00-00')
        birth_date = form_data.get('birth_date')
        
        try:
            if role == 'athlete':
                Athlete.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'birth_date': birth_date,
                        'phone': phone,
                    }
                )
            elif role == 'parent':
                Parent.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'birth_date': birth_date,
                        'phone': phone,
                    }
                )
            elif role == 'trainer':
                Trainer.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'birth_date': birth_date,
                        'phone': phone,
                    }
                )
            elif role == 'staff':
                Staff.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'birth_date': birth_date,
                        'phone': phone,
                        'role': 'manager',  # Default staff role
                    }
                )
            print(f"✅ Created {role} profile for user {user.username}")
        except Exception as e:
            print(f"❌ Error creating profile for {user.username} with role {role}: {e}")


def register_done_view(request: HttpRequest) -> HttpResponse:
    """Registration completion page"""
    return render(request, 'admin/core/registration/done.html', {
        'title': 'Registration Complete',
        'opts': User._meta,
    })


def register_cancel_view(request: HttpRequest) -> HttpResponse:
    """Cancel registration"""
    draft_id = request.session.get('draft_id')
    if draft_id:
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
            draft.safe_dispose()
        except RegistrationDraft.DoesNotExist:
            pass
        request.session.pop('draft_id', None)
    
    messages.info(request, "Registration cancelled.")
    return HttpResponseRedirect(reverse('admin:auth_user_changelist'))
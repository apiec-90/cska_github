"""
Админки пользователей: Trainer, Staff, Parent, Athlete.
Используют базовые классы для устранения дублирования кода.
"""
from django.contrib import admin
from django.db import models
from django.utils.html import format_html

from core.models import (
    Trainer, Staff, Parent, Athlete, 
    TrainingGroup, AthleteTrainingGroup, AthleteParent
)
from .base import (
    BasePersonAdmin, BaseDocumentMixin, BaseChangeFormMixin,
    AthleteParentInline, AthleteTrainingGroupInline, ParentAthleteInline
)


@admin.register(Trainer)
class TrainerAdmin(BaseDocumentMixin, BasePersonAdmin, BaseChangeFormMixin):
    """Админка тренеров с поддержкой документов"""
    
    list_display = [
        'get_full_name', 'get_phone', 'birth_date', 
        'get_groups_display', 'get_athletes_count', 
        'get_active_status', 'is_archived'
    ]
    list_filter = ['is_archived', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'phone']
    ordering = ['user__last_name', 'user__first_name']
    
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
    
    change_form_template = 'admin/core/trainer/change_form.html'

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
        """Оптимизация запросов"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('traininggroup_set')
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Добавляем группы тренера в контекст"""
        extra_context = extra_context or {}
        trainer_groups = []
        
        if object_id:
            try:
                trainer = Trainer.objects.get(pk=object_id)
                trainer_groups = trainer.traininggroup_set.prefetch_related(
                    'groupschedule_set',
                    'athletetraininggroup_set__athlete'
                ).all()
            except Trainer.DoesNotExist:
                pass
        
        extra_context['trainer_groups'] = trainer_groups
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(Staff)
class StaffAdmin(BasePersonAdmin):
    """Админка сотрудников"""
    
    list_display = [
        'get_full_name', 'get_role_display', 'get_phone', 
        'birth_date', 'get_active_status', 'is_archived'
    ]
    list_filter = ['role', 'is_archived', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'phone']
    ordering = ['user__last_name', 'user__first_name']
    
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

    def get_role_display(self, obj):
        """Отображение роли сотрудника"""
        return obj.get_role_display()
    get_role_display.short_description = "Роль"


@admin.register(Parent)
class ParentAdmin(BaseDocumentMixin, BasePersonAdmin, BaseChangeFormMixin):
    """Админка родителей с поддержкой документов"""
    
    list_display = [
        'get_full_name', 'get_phone', 'birth_date', 
        'get_children_display', 'get_active_status', 'is_archived'
    ]
    list_filter = ['is_archived', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'phone']
    ordering = ['user__last_name', 'user__first_name']
    
    # inlines = [ParentAthleteInline]  # Отключены - используем кастомные блоки в шаблоне
    change_form_template = 'admin/core/parent/change_form.html'
    
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
    
    def get_children_display(self, obj):
        """Дети родителя с ФИО"""
        rels = obj.get_children_relations()
        if rels:
            children_names = []
            for rel in rels:
                first_name = (rel.athlete.first_name or rel.athlete.user.first_name or "")
                last_name = (rel.athlete.last_name or rel.athlete.user.last_name or "")
                child_name = f"{last_name} {first_name}".strip()
                if not child_name:
                    child_name = rel.athlete.user.username
                children_names.append(child_name)
            return ", ".join(children_names)
        return "Детей нет"
    get_children_display.short_description = "Дети"
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('athleteparent_set__athlete__user')
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Добавляем детей родителя в контекст"""
        extra_context = extra_context or {}
        parent_children = []
        
        if object_id:
            try:
                parent = Parent.objects.get(pk=object_id)
                parent_children = parent.get_children_relations().select_related(
                    'athlete__user'
                ).prefetch_related(
                    'athlete__athletetraininggroup_set__training_group__trainer__user',
                    'athlete__athletetraininggroup_set__training_group__groupschedule_set'
                )
            except Parent.DoesNotExist:
                pass
        
        extra_context['parent_children'] = parent_children
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(Athlete)
class AthleteAdmin(BaseDocumentMixin, BasePersonAdmin, BaseChangeFormMixin):
    """Админка спортсменов с поддержкой документов"""
    
    list_display = [
        'get_full_name', 'get_phone', 'birth_date', 
        'get_groups_display', 'get_parents_display', 
        'get_active_status', 'is_archived'
    ]
    list_filter = ['is_archived', 'birth_date', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'phone']
    ordering = ['user__last_name', 'user__first_name']
    
    # inlines = [AthleteParentInline, AthleteTrainingGroupInline]  # Отключены - используем кастомные блоки в шаблоне
    change_form_template = 'admin/core/athlete/change_form.html'
    
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
    
    def get_groups_display(self, obj):
        """Группы спортсмена"""
        groups = obj.athletetraininggroup_set.select_related('training_group').all()
        if groups:
            group_names = [atg.training_group.name for atg in groups]
            return ", ".join(group_names)
        return "Групп нет"
    get_groups_display.short_description = "Группы"
    
    def get_parents_display(self, obj):
        """Родители спортсмена"""
        parents = obj.athleteparent_set.select_related('parent__user').all()
        if parents:
            parent_names = []
            for ap in parents:
                first_name = (ap.parent.first_name or ap.parent.user.first_name or "")
                last_name = (ap.parent.last_name or ap.parent.user.last_name or "")
                parent_name = f"{last_name} {first_name}".strip()
                if not parent_name:
                    parent_name = ap.parent.user.username
                parent_names.append(parent_name)
            return ", ".join(parent_names)
        return "Родителей нет"
    get_parents_display.short_description = "Родители"
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            'athletetraininggroup_set__training_group',
            'athleteparent_set__parent__user'
        )
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Добавляем группы и родителей спортсмена в контекст"""
        extra_context = extra_context or {}
        athlete_groups = []
        athlete_parents = []
        
        if object_id:
            try:
                athlete = Athlete.objects.get(pk=object_id)
                
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
            'athlete_groups': athlete_groups,
            'athlete_parents': athlete_parents,
        })
        return super().changeform_view(request, object_id, form_url, extra_context)
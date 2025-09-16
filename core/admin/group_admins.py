"""  
Админки групп, расписания и связанных сущностей.
"""
from django.contrib import admin
import logging
from django.shortcuts import redirect, get_object_or_404
from django.urls import path, reverse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.template.response import TemplateResponse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.html import format_html
from datetime import datetime

from core.models import (
    TrainingGroup, GroupSchedule, TrainingSession, 
    AttendanceRecord, Trainer, Athlete, AthleteTrainingGroup
)
from core.forms import GroupScheduleForm  # noqa: F401 - referenced by admin templates
from core.utils.sessions import ensure_month_sessions_for_group, resync_future_sessions_for_group
from core.utils.enhanced_sessions import ensure_yearly_sessions_for_group, auto_ensure_yearly_schedule

# CLEANUP: use logging instead of print for internal diagnostics
logger = logging.getLogger(__name__)


class GroupScheduleInline(admin.TabularInline):
    """Inline для расписания группы"""
    model = GroupSchedule
    extra = 1
    fields = ('weekday', 'start_time', 'end_time')
    verbose_name = "Расписание"
    verbose_name_plural = "Расписание группы"

    def get_weekday_display(self, obj):
        """Отображение дня недели"""
        weekday_names = {
            1: 'Понедельник', 2: 'Вторник', 3: 'Среда',
            4: 'Четверг', 5: 'Пятница', 6: 'Суббота', 7: 'Воскресенье'
        }
        return weekday_names.get(obj.weekday, f"День {obj.weekday}")


@admin.register(TrainingGroup)
class TrainingGroupAdmin(admin.ModelAdmin):
    """Админка тренировочных групп с расширенным функционалом"""
    
    list_display = [
        'name', 'trainer', 'get_age_range', 'get_athletes_count', 
        'get_parents_count', 'is_active', 'is_archived'
    ]
    list_filter = ['trainer', 'is_active', 'is_archived', 'age_min', 'age_max']
    search_fields = ['name', 'trainer__user__first_name', 'trainer__user__last_name']
    ordering = ['name']
    list_per_page = 25
    
    inlines = [GroupScheduleInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'trainer', 'age_min', 'age_max', 'max_athletes')
        }),
        ('Статус', {
            'fields': ('is_active', 'is_archived', 'archived_at', 'archived_by'),
            'classes': ('collapse',),
        }),
    )
    
    @admin.display(description="Возраст")
    def get_age_range(self, obj):
        """Возрастной диапазон группы"""
        return f"{obj.age_min}-{obj.age_max} лет"
    
    @admin.display(description="Спортсменов")
    def get_athletes_count(self, obj):
        """Количество спортсменов в группе"""
        count = obj.get_athletes_count()
        max_count = obj.max_athletes
        if count >= max_count:
            return format_html('<span style="color: red;">{}/{}</span>', count, max_count)
        elif count >= max_count * 0.8:
            return format_html('<span style="color: orange;">{}/{}</span>', count, max_count)
        else:
            return f"{count}/{max_count}"
    
    @admin.display(description="Родителей")
    def get_parents_count(self, obj):
        """Количество родителей в группе"""
        return obj.get_parents_count()
    
    def get_queryset(self, request):
        """Оптимизация запросов для списка групп.
        Загружаем тренера и его пользователя, чтобы избежать N+1 в list_display/str().
        """
        qs = super().get_queryset(request)
        return qs.select_related('trainer__user')
    
    def get_urls(self):
        """Добавляем кастомные URLs"""
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        custom_urls = [
            path('create-wizard/', self.admin_site.admin_view(self.create_wizard_view), 
                 name='%s_%s_create_wizard' % info),
            path('create-wizard/<str:step>/', self.admin_site.admin_view(self.create_step_view), 
                 name='%s_%s_create_step' % info),
            path('<path:object_id>/schedule/', self.admin_site.admin_view(self.schedule_view), 
                 name='%s_%s_schedule' % info),
            path('<path:object_id>/journal/', self.admin_site.admin_view(self.journal_view), 
                 name='%s_%s_journal' % info),
            path('<path:object_id>/panel/', self.admin_site.admin_view(self.panel_view), 
                 name='%s_%s_panel' % info),
            path('<path:object_id>/edit/', self.admin_site.admin_view(self.edit_group_view), 
                 name='%s_%s_edit' % info),
            path('<path:object_id>/children/', self.admin_site.admin_view(self.children_view), 
                 name='%s_%s_children' % info),
        ]
        return custom_urls + urls
    
    def create_wizard_view(self, request):
        """Мастер создания группы - шаг 1"""
        if not self.has_add_permission(request):
            raise PermissionDenied

        if request.method == "POST":
            # Сохраняем данные в сессии для следующего шага
            group_data = {
                'name': request.POST.get('name'),
                'trainer_id': request.POST.get('trainer'),
                'age_min': request.POST.get('age_min'),
                'age_max': request.POST.get('age_max'),
                'max_athletes': request.POST.get('max_athletes'),
                'is_active': request.POST.get('is_active') == 'on'
            }
            request.session['group_create_data'] = group_data
            return redirect(reverse("admin:core_traininggroup_create_step", args=["schedule"]))

        # Получаем активных тренеров
        trainers = Trainer.objects.filter(is_archived=False).select_related('user')  # type: ignore
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
                with transaction.atomic():  # type: ignore[misc]
                    # Создаем группу
                    trainer = Trainer.objects.get(pk=group_data['trainer_id']) if group_data['trainer_id'] else None  # type: ignore[attr-defined]
                    group = TrainingGroup.objects.create(  # type: ignore[attr-defined]
                        name=group_data['name'],
                        trainer=trainer,
                        age_min=group_data['age_min'] or 0,
                        age_max=group_data['age_max'] or 100,
                        max_athletes=group_data['max_athletes'] or 20,
                        is_active=group_data['is_active']
                    )
                    
                    # Создаем расписание
                    for weekday in weekdays:
                        GroupSchedule.objects.create(  # type: ignore[attr-defined]
                            training_group=group,
                            weekday=weekday,
                            start_time=start_time,
                            end_time=end_time
                        )
                    
                    # Генерируем сессии на текущий месяц
                    sessions_created = ensure_month_sessions_for_group(group)
                    
                    # Очищаем данные из сессии
                    request.session.pop('group_create_data', None)
                    
                    messages.success(
                        request, 
                        f'Группа "{group.name}" создана. Создано {sessions_created} тренировочных сессий.'
                    )
                    return redirect('admin:core_traininggroup_change', object_id=group.pk)
            else:
                messages.error(request, "Заполните все поля расписания")

        ctx = {
            **self.admin_site.each_context(request),
            "title": "Создать группу - Шаг 2: Расписание",
            "opts": self.model._meta,
            "group_data": group_data,
            "step": "schedule",
            "weekdays": range(1, 8),  # 1-7 для дней недели
        }
        return TemplateResponse(request, "admin/core/traininggroup/create_wizard.html", ctx)

    def schedule_view(self, request, object_id):
        """Просмотр и редактирование расписания группы"""
        group = get_object_or_404(TrainingGroup, pk=object_id)
        
        if not self.has_view_permission(request, group):
            raise PermissionDenied
            
        if request.method == "POST":
            if not self.has_change_permission(request, group):
                raise PermissionDenied
                
            # Обработка добавления расписания
            action = request.POST.get('action')
            
            if action == 'add_schedule':
                weekday = request.POST.get('weekday')
                start_time = request.POST.get('start_time')
                end_time = request.POST.get('end_time')
                
                if weekday and start_time and end_time:
                    schedule, created = GroupSchedule.objects.get_or_create(  # type: ignore[attr-defined]
                        training_group=group,
                        weekday=int(weekday),
                        defaults={
                            'start_time': start_time,
                            'end_time': end_time
                        }
                    )
                    if created:
                        messages.success(request, 'Расписание добавлено')
                        # Пересинхронизируем сессии
                        resync_future_sessions_for_group(group)
                    else:
                        messages.warning(request, 'Расписание на этот день уже существует')
                else:
                    messages.error(request, 'Заполните все поля')
                    
            elif action == 'delete_schedule':
                schedule_id = request.POST.get('schedule_id')
                if schedule_id:
                    try:
                        schedule = GroupSchedule.objects.get(pk=schedule_id, training_group=group)  # type: ignore[attr-defined]
                        schedule.delete()
                        messages.success(request, 'Расписание удалено')
                        # Пересинхронизируем сессии
                        resync_future_sessions_for_group(group)
                    except GroupSchedule.DoesNotExist:  # type: ignore[attr-defined]
                        messages.error(request, 'Расписание не найдено')
                        
            return redirect('admin:core_traininggroup_schedule', object_id=object_id)
        
        schedules = group.groupschedule_set.all().order_by('weekday', 'start_time')
        
        # Дни недели для выбора
        weekday_choices = [
            (1, 'Понедельник'),
            (2, 'Вторник'),
            (3, 'Среда'),
            (4, 'Четверг'),
            (5, 'Пятница'),
            (6, 'Суббота'),
            (7, 'Воскресенье'),
        ]
        
        ctx = {
            **self.admin_site.each_context(request),
            "title": f"Расписание группы {group.name}",
            "opts": self.model._meta,
            "object": group,
            "schedules": schedules,
            "weekday_choices": weekday_choices,
        }
        return TemplateResponse(request, "admin/core/traininggroup/schedule.html", ctx)

    def journal_view(self, request, object_id):
        """Журнал посещаемости группы"""
        import json
        from datetime import date  # CLEANUP: datetime already imported at module level
        from calendar import monthrange
        
        group = get_object_or_404(TrainingGroup, pk=object_id)
        
        if not self.has_view_permission(request, group):
            raise PermissionDenied
        
        # Получаем параметры из URL
        current_year = int(request.GET.get('year', timezone.localdate().year))
        current_month = int(request.GET.get('month', timezone.localdate().month))
        edit_mode = request.GET.get('edit') == '1'

        # Убираем кэширование контекста из-за PicklingError с объектами Django
        
        if request.method == "POST":
            if not self.has_change_permission(request, group):
                raise PermissionDenied
            
            # Массовое обновление посещаемости
            if request.POST.get('action') == 'bulk_update_attendance':
                try:
                    changes_json = request.POST.get('changes', '[]')
                    changes = json.loads(changes_json)
                    updated_count = 0
                    
                    for change in changes:
                        session_id = change.get('session_id')
                        athlete_id = change.get('athlete_id')
                        present = change.get('present', False)
                        
                        try:
                            # Получаем объект Staff для текущего пользователя
                            marked_by_staff = None
                            try:
                                if hasattr(request.user, 'staff'):
                                    marked_by_staff = request.user.staff
                                else:
                                    # Получаем любого staff для обязательного поля
                                    from core.models import Staff
                                    marked_by_staff = Staff.objects.first()  # type: ignore[attr-defined]
                            except Exception:
                                from core.models import Staff
                                marked_by_staff = Staff.objects.first()  # type: ignore[attr-defined]
                            
                            # Получаем или создаем запись посещаемости
                            attendance, created = AttendanceRecord.objects.get_or_create(  # type: ignore[attr-defined]
                                session_id=session_id,
                                athlete_id=athlete_id,
                                defaults={
                                    'was_present': present,
                                    'marked_by': marked_by_staff
                                }
                            )
                            
                            if not created:
                                # Обновляем существующую запись
                                attendance.was_present = present
                                if marked_by_staff:
                                    attendance.marked_by = marked_by_staff
                                attendance.save()
                            
                            updated_count += 1
                            
                        except Exception as e:
                            logger.exception(f"CLEANUP: Ошибка обновления записи: {e}")
                            continue
                    
                    return JsonResponse({
                        'success': True,
                        'updated_count': updated_count,
                        'message': f'Обновлено {updated_count} записей'
                    })
                    
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            # Генерация расписания до конца года
            if request.POST.get('action') == 'generate_yearly_schedule':
                try:
                    sessions_created = ensure_yearly_sessions_for_group(group)
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Создано {sessions_created} сессий',
                        'sessions_created': sessions_created
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'message': f'Ошибка: {e}'
                    })
        
        # GET запрос - отображаем журнал
        # АВТОМАТИЧЕСКИ ОБЕСПЕЧИВАЕМ НАЛИЧИЕ СЕССИЙ НА ВЕСЬ ГОД
        try:
            _ = auto_ensure_yearly_schedule(group)  # CLEANUP: ignore value; side-effect only
        except Exception:
            _ = 0
        
        # Получаем всех спортсменов группы
        children = Athlete.objects.filter(  # type: ignore[attr-defined]
            athletetraininggroup__training_group=group
        ).select_related('user').order_by('user__last_name', 'user__first_name')
        
        # Получаем сессии за выбранный месяц
        start_date = date(current_year, current_month, 1)
        end_date = date(current_year, current_month, monthrange(current_year, current_month)[1])
        
        sessions = TrainingSession.objects.filter(  # type: ignore[attr-defined]
            training_group=group,
            date__range=[start_date, end_date]
        ).order_by('date', 'start_time')
        
        # Получаем все записи посещаемости для текущего месяца
        attendance_records = AttendanceRecord.objects.filter(  # type: ignore[attr-defined]
            session__in=sessions,
            athlete__in=children
        ).select_related('session', 'athlete')
        
        # Создаем словарь посещаемости: {session_id: {athlete_id: True/False}}
        present = {}
        for record in attendance_records:
            session_id = record.session.id
            athlete_id = record.athlete.id
            if session_id not in present:
                present[session_id] = {}
            present[session_id][athlete_id] = record.was_present
        
        # Определяем состояние сессий
        now = timezone.now()
        today = timezone.localdate()
        
        sessions_data = []
        for session in sessions:
            session_datetime = timezone.make_aware(
                datetime.combine(session.date, session.start_time)
            )
            
            if session.is_canceled:
                state = 'canceled'
            elif session.date > today:
                state = 'future'
            elif session.date < today:
                state = 'past'
            elif session.date == today:
                if session_datetime <= now <= timezone.make_aware(
                    datetime.combine(session.date, session.end_time)
                ):
                    state = 'active'
                elif now > timezone.make_aware(
                    datetime.combine(session.date, session.end_time)
                ):
                    state = 'closed'
                else:
                    state = 'future'
            else:
                state = 'future'
            
            sessions_data.append({
                'id': session.id,
                'date': session.date,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'is_canceled': session.is_canceled,
                'state': state,
                'editable': state in ['past', 'closed'] or edit_mode  # Редактировать можно прошлые/закрытые или в режиме редактирования
            })
        
        # Навигация по месяцам
        prev_month = current_month - 1
        prev_year = current_year
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1
        
        next_month = current_month + 1
        next_year = current_year
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        month_names = [
            '', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        
        month_nav = {
            'current': {
                'year': current_year,
                'month': current_month,
                'name': month_names[current_month]
            },
            'prev': {
                'year': prev_year,
                'month': prev_month,
                'name': month_names[prev_month]
            },
            'next': {
                'year': next_year,
                'month': next_month,
                'name': month_names[next_month]
            }
        }
        
        # Статистика
        statistics = {
            'total': sessions.count(),
            'active': len([s for s in sessions_data if s['state'] == 'active']),
            'closed': len([s for s in sessions_data if s['state'] == 'closed']),
            'future': len([s for s in sessions_data if s['state'] == 'future']),
            'canceled': len([s for s in sessions_data if s['is_canceled']])
        }
        
        ctx = {
            **self.admin_site.each_context(request),
            "title": f"Журнал группы {group.name}",
            "opts": self.model._meta,
            "object": group,
            "group": group,
            "children": children,
            "sessions": sessions_data,
            "present": present,
            "current_year": current_year,
            "current_month": current_month,
            "edit_mode": edit_mode,
            "month_nav": month_nav,
            "statistics": statistics,
        }
        return TemplateResponse(request, "admin/core/traininggroup/journal_unified.html", ctx)

    def panel_view(self, request, object_id):
        """Панель управления группой"""
        try:
            group = get_object_or_404(TrainingGroup, pk=object_id)
            
            if not self.has_view_permission(request, group):
                raise PermissionDenied
            
            # Получаем спортсменов в группе
            children = Athlete.objects.filter(  # type: ignore[attr-defined]
                athletetraininggroup__training_group=group
            ).select_related('user')
            
            # Получаем расписание
            schedule_details = group.groupschedule_set.all().order_by('weekday', 'start_time')
            
            # Следующая тренировка
            next_session = None
            try:
                next_session = TrainingSession.objects.filter(  # type: ignore[attr-defined]
                    training_group=group,
                    date__gte=timezone.localdate()
                ).order_by('date', 'start_time').first()
            except Exception:
                pass  # Не критично, если нет сессий
            
            # Статистика
            children_count = children.count()
            schedule_count = schedule_details.count()
            
            # Создаем контекст без ошибок
            try:
                base_context = self.admin_site.each_context(request)
            except Exception:
                # Фолбэк контекст если each_context не работает
                base_context = {
                    'request': request,
                    'user': request.user,
                    'admin_url': '/admin/',
                }
            
            ctx = {
                **base_context,
                "title": f"Группа: {group.name}",
                "opts": self.model._meta,
                "object": group,
                "group": group,
                "children": children,
                "schedule_details": schedule_details,
                "header": {
                    "name": group.name,
                    "trainer": str(group.trainer) if group.trainer else None,
                    "children_count": children_count,
                    "schedule_count": schedule_count,
                    "next_session": next_session,
                    "urls": {
                        "edit": reverse("admin:core_traininggroup_change", args=[group.id]),
                        "children": reverse("admin:core_traininggroup_children", args=[group.id]),
                        "schedule": reverse("admin:core_traininggroup_schedule", args=[group.id]),
                        "journal": reverse("admin:core_traininggroup_journal", args=[group.id]),
                    }
                },
            }
            return TemplateResponse(request, "admin/core/traininggroup/panel.html", ctx)
            
        except Exception as e:
            messages.error(request, f'Ошибка при загрузке панели группы: {e}')
            return redirect(reverse("admin:core_traininggroup_changelist"))

    def edit_group_view(self, request, object_id):
        """Редактирование группы"""
        group = get_object_or_404(TrainingGroup, pk=object_id)
        
        if not self.has_change_permission(request, group):
            raise PermissionDenied
        
        # Используем стандартный Django admin change view без переопределения
        return super().change_view(request, object_id)

    def change_view(self, request, object_id, form_url="", extra_context=None) -> HttpResponseRedirect:
        """Перенаправляем на панель группы"""
        # Проверяем, что группа существует
        try:
            get_object_or_404(TrainingGroup, pk=object_id)  # CLEANUP: existence check only
            return HttpResponseRedirect(reverse("admin:core_traininggroup_panel", args=[object_id]))
        except Exception as e:
            messages.error(request, f'Ошибка при открытии группы: {e}')
            return HttpResponseRedirect(reverse("admin:core_traininggroup_changelist"))
    
    def add_view(self, request, form_url="", extra_context=None) -> HttpResponseRedirect:
        """Перенаправляем на мастер создания группы"""
        return HttpResponseRedirect(reverse("admin:core_traininggroup_create_wizard"))

    def children_view(self, request, object_id):
        """Управление детьми в группе"""
        group = get_object_or_404(TrainingGroup, pk=object_id)
        
        if not self.has_view_permission(request, group):
            raise PermissionDenied
            
        if request.method == "POST":
            if not self.has_change_permission(request, group):
                raise PermissionDenied
                
            # Добавление спортсмена
            athlete_id = request.POST.get('athlete_id')
            if athlete_id:
                try:
                    athlete = Athlete.objects.get(pk=athlete_id)  # type: ignore[attr-defined]
                    relation, created = AthleteTrainingGroup.objects.get_or_create(  # type: ignore[attr-defined]
                        athlete=athlete,
                        training_group=group
                    )
                    if created:
                        messages.success(request, f'Спортсмен {athlete} добавлен в группу')
                    else:
                        messages.warning(request, f'Спортсмен {athlete} уже в группе')
                except Athlete.DoesNotExist:  # type: ignore[attr-defined]
                    messages.error(request, 'Спортсмен не найден')
            
            # Удаление спортсмена
            remove_id = request.POST.get('remove_id')
            if remove_id:
                try:
                    athlete = Athlete.objects.get(pk=remove_id)  # type: ignore[attr-defined]
                    AthleteTrainingGroup.objects.filter(  # type: ignore[attr-defined]
                        athlete=athlete,
                        training_group=group
                    ).delete()
                    messages.success(request, f'Спортсмен {athlete} удален из группы')
                except Athlete.DoesNotExist:  # type: ignore[attr-defined]
                    messages.error(request, 'Спортсмен не найден')
                    
            return redirect('admin:core_traininggroup_children', object_id=object_id)
        
        # Спортсмены в группе
        members = Athlete.objects.filter(  # type: ignore[attr-defined]
            athletetraininggroup__training_group=group
        ).select_related('user')
        
        # Доступные спортсмены (не в этой группе)
        current_athlete_ids = members.values_list('id', flat=True)
        available_athletes = Athlete.objects.filter(  # type: ignore[attr-defined]
            is_archived=False
        ).exclude(
            id__in=current_athlete_ids
        ).select_related('user').order_by('user__last_name', 'user__first_name')
        
        ctx = {
            **self.admin_site.each_context(request),
            "title": f"Дети группы: {group.name}",
            "opts": self.model._meta,
            "group": group,
            "members": members,
            "available_athletes": available_athletes,
        }
        return TemplateResponse(request, "admin/core/traininggroup/children.html", ctx)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Админка записей посещаемости"""
    
    list_display = ['athlete', 'session', 'was_present', 'marked_at', 'marked_by']
    list_filter = ['was_present', 'marked_at', 'session__training_group']
    search_fields = [
        'athlete__user__first_name', 'athlete__user__last_name', 
        'session__training_group__name'
    ]
    ordering = ['-marked_at', 'athlete__user__last_name']
    
    change_list_template = 'admin/core/attendancerecord/change_list.html'
    change_form_template = 'admin/core/attendancerecord/change_form.html'

    def get_queryset(self, request):
        """Оптимизация: предзагружаем связанные объекты для колонок."""
        qs = super().get_queryset(request)
        return qs.select_related('athlete__user', 'session__training_group', 'marked_by__user')


# Inline для записей посещаемости в сессии
class AttendanceRecordInline(admin.TabularInline):
    """Inline записей посещаемости в тренировочной сессии"""
    model = AttendanceRecord
    extra = 0
    fields = ('athlete', 'was_present', 'marked_by')
    readonly_fields = ('marked_by',)


# TrainingSession скрыта из меню - управляем через TrainingGroup
try:
    admin.site.unregister(TrainingSession)
except Exception:  # CLEANUP: avoid bare except
    pass  # TrainingSession not registered


class TrainingSessionAdmin(admin.ModelAdmin):
    """Админка тренировочных сессий (скрыта из меню)"""
    
    list_display = ['training_group', 'date', 'start_time', 'end_time', 'is_closed', 'is_canceled']
    list_filter = ['training_group', 'date', 'is_closed', 'is_canceled']
    search_fields = ['training_group__name']
    ordering = ['-date', 'training_group__name']
    inlines = [AttendanceRecordInline]
    
    change_form_template = 'admin/core/trainingsession/change_form.html'

    def get_queryset(self, request):
        """Оптимизация: загружаем группу и тренера (и его пользователя)."""
        qs = super().get_queryset(request)
        return qs.select_related('training_group__trainer__user')
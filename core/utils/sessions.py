from datetime import timedelta, date
from django.utils import timezone
from django.db import transaction
from ..models import GroupSchedule, TrainingSession, TrainingGroup

def month_bounds(d: date):
    """Возвращает границы месяца для заданной даты"""
    first = d.replace(day=1)
    next_first = (first.replace(year=first.year+1, month=1, day=1)
                  if first.month==12 else first.replace(month=first.month+1, day=1))
    return first, next_first

def ensure_month_sessions_for_group(group, target_date=None):
    """Создает тренировочные сессии для группы на указанный месяц (по умолчанию - текущий)"""
    if target_date is None:
        target_date = timezone.localdate()
    
    first, next_first = month_bounds(target_date)
    schedules = list(GroupSchedule.objects.filter(training_group=group))
    
    # Получаем существующие сессии для этого месяца
    existing = set(TrainingSession.objects
                   .filter(training_group=group, date__gte=first, date__lt=next_first)
                   .values_list("date", "start_time"))
    
    created = 0
    d = first
    
    with transaction.atomic():
        while d < next_first:
            for sch in schedules:
                # sch.weekday: 1-7 (Пн-Вс), d.weekday(): 0-6 (Пн-Вс)
                # Преобразуем sch.weekday в формат Python
                python_weekday = sch.weekday - 1
                if d.weekday() == python_weekday:
                    key = (d, sch.start_time)
                    if key not in existing:
                        TrainingSession.objects.create(
                            training_group=group,
                            date=d,
                            start_time=sch.start_time,
                            end_time=sch.end_time,
                            is_closed=False,
                            is_canceled=False
                        )
                        created += 1
            d += timedelta(days=1)
    
    return created

def resync_future_sessions_for_group(group):
    """Пересобирает будущие незакрытые тренировочные сессии для группы"""
    today = timezone.localdate()
    schedules = list(GroupSchedule.objects.filter(training_group=group))
    
    with transaction.atomic():
        # 1) удалить будущие незакрытые сессии, не соответствующие актуальному расписанию
        future_sessions = TrainingSession.objects.filter(
            training_group=group, 
            date__gte=today, 
            is_closed=False
        )
        
        for session in future_sessions:
            # Проверяем, соответствует ли сессия актуальному расписанию
            # sch.weekday: 1-7 (Пн-Вс), session.date.weekday(): 0-6 (Пн-Вс)
            ok = any(
                session.date.weekday() == (sch.weekday - 1) and 
                session.start_time == sch.start_time 
                for sch in schedules
            )
            if not ok:
                session.delete()
        
        # 2) досоздать недостающие сессии на остаток текущего месяца
        ensure_month_sessions_for_group(group)

def ensure_next_month_sessions_for_group(group):
    """Создает тренировочные сессии для группы на следующий месяц"""
    today = timezone.localdate()
    next_month = today.replace(day=1) + timedelta(days=32)
    next_month = next_month.replace(day=1)
    
    return ensure_month_sessions_for_group(group, next_month)

def cleanup_old_sessions():
    """Удаляет старые тренировочные сессии (старше 1 года)"""
    cutoff_date = timezone.localdate() - timedelta(days=365)
    deleted_count = TrainingSession.objects.filter(date__lt=cutoff_date).delete()[0]
    return deleted_count

def ensure_next_month_sessions_for_all_groups():
    """Создает тренировочные сессии на следующий месяц для всех активных групп"""
    from ..models import TrainingGroup
    
    total_created = 0
    groups = TrainingGroup.objects.filter(is_archived=False)
    
    for group in groups:
        if group.schedules.exists():
            try:
                created = ensure_next_month_sessions_for_group(group)
                total_created += created
            except Exception as e:
                print(f"Ошибка при создании сессий для группы {group}: {e}")
    
    return total_created

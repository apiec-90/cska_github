from datetime import timedelta, date
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from ..models import GroupSchedule, TrainingSession

def get_session_state(session, current_time=None):
    """
    Определяет состояние сессии на основе времени и статуса
    Возвращает: 'active', 'closed', 'future', 'past', 'canceled'
    """
    if current_time is None:
        current_time = timezone.now()
    
    current_date = current_time.date()
    current_time_only = current_time.time()
    
    # Отмененная сессия
    if session.is_canceled:
        return 'canceled'
    
    # Закрытая сессия
    if session.is_closed:
        return 'closed'
    
    # Будущая дата
    if session.date > current_date:
        return 'future'
    
    # Прошедшая дата
    if session.date < current_date:
        return 'past'
    
    # Сегодняшняя дата - проверяем время
    if session.date == current_date:
        # Если тренировка еще не началась
        if current_time_only < session.start_time:
            return 'future'
        
        # Если тренировка идет сейчас
        if session.start_time <= current_time_only <= session.end_time:
            return 'active'
        
        # Если тренировка уже закончилась
        if current_time_only > session.end_time:
            return 'past'
    
    return 'past'

def is_session_editable(session, edit_mode=False, current_time=None):
    """
    Определяет, можно ли редактировать отметки в сессии
    """
    if edit_mode:
        # В режиме редактирования можно редактировать все кроме отмененных
        return not getattr(session, 'is_canceled', False)
    
    state = get_session_state(session, current_time)
    
    # Можно редактировать только активные сессии и сегодняшние прошедшие
    return state in ['active', 'past'] and session.date == timezone.localdate()

def ensure_yearly_sessions_for_group(group, start_date=None):
    """
    Создает тренировочные сессии для группы до конца года
    При наступлении нового года автоматически создает на новый год
    """
    if start_date is None:
        start_date = timezone.localdate()
    
    # Определяем конец года - если мы в новом году, создаем сессии на весь год вперед
    end_of_year = date(start_date.year, 12, 31)
    
    schedules = list(GroupSchedule.objects.filter(training_group=group))
    if not schedules:
        return 0
    
    # Получаем все существующие сессии до конца года
    existing = set(TrainingSession.objects
                   .filter(training_group=group, 
                          date__gte=start_date, 
                          date__lte=end_of_year)
                   .values_list("date", "start_time"))
    
    created = 0
    current_date = start_date
    
    with transaction.atomic():
        while current_date <= end_of_year:
            for schedule in schedules:
                # Преобразуем weekday из модели (1-7) в Python (0-6)
                python_weekday = schedule.weekday - 1
                
                if current_date.weekday() == python_weekday:
                    key = (current_date, schedule.start_time)
                    
                    if key not in existing:
                        TrainingSession.objects.create(
                            training_group=group,
                            date=current_date,
                            start_time=schedule.start_time,
                            end_time=schedule.end_time,
                            is_closed=False,
                            is_canceled=False
                        )
                        created += 1
            
            current_date += timedelta(days=1)
    
    return created

def get_sessions_for_month(group, year, month):
    """
    Получает все сессии группы за указанный месяц
    """
    start_date = date(year, month, 1)
    
    # Последний день месяца
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    return TrainingSession.objects.filter(
        training_group=group,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date', 'start_time')

def resync_future_sessions_from_date(group, from_date=None):
    """
    Пересинхронизирует будущие сессии начиная с указанной даты
    Сохраняет закрытые и прошедшие сессии
    """
    if from_date is None:
        from_date = timezone.localdate()
    
    schedules = list(GroupSchedule.objects.filter(training_group=group))
    
    with transaction.atomic():
        # Удаляем будущие незакрытые сессии, не соответствующие расписанию
        future_sessions = TrainingSession.objects.filter(
            training_group=group,
            date__gte=from_date,
            is_closed=False
        )
        
        sessions_to_delete = []
        
        for session in future_sessions:
            # Проверяем соответствие расписанию
            matches_schedule = any(
                session.date.weekday() == (sch.weekday - 1) and 
                session.start_time == sch.start_time and
                session.end_time == sch.end_time
                for sch in schedules
            )
            
            if not matches_schedule:
                sessions_to_delete.append(session.id)
        
        # Удаляем несоответствующие сессии
        if sessions_to_delete:
            TrainingSession.objects.filter(id__in=sessions_to_delete).delete()
        
        # Создаем недостающие сессии до конца года
        return ensure_yearly_sessions_for_group(group, from_date)

def get_month_navigation_data(current_year, current_month):
    """
    Генерирует данные для навигации по месяцам
    """
    today = timezone.localdate()
    
    # Предыдущий месяц
    if current_month == 1:
        prev_year, prev_month = current_year - 1, 12
    else:
        prev_year, prev_month = current_year, current_month - 1
    
    # Следующий месяц
    if current_month == 12:
        next_year, next_month = current_year + 1, 1
    else:
        next_year, next_month = current_year, current_month + 1
    
    # Названия месяцев
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    
    return {
        'current': {
            'year': current_year,
            'month': current_month,
            'name': month_names[current_month],
            'is_current': current_year == today.year and current_month == today.month
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
        },
        'available_months': [
            {
                'year': today.year,
                'month': m,
                'name': month_names[m],
                'is_current': m == today.month
            }
            for m in range(1, 13)
        ]
    }

def close_session(session, closed_by_staff=None):
    """
    Закрывает сессию и устанавливает кто закрыл
    """
    session.is_closed = True
    if hasattr(session, 'closed_by') and closed_by_staff:
        session.closed_by = closed_by_staff
    session.save(update_fields=['is_closed'])
    return session

def cancel_session(session, reason="", canceled_by_staff=None):
    """
    Отменяет сессию
    """
    session.is_canceled = True
    if hasattr(session, 'cancel_reason'):
        session.cancel_reason = reason
    if hasattr(session, 'canceled_by') and canceled_by_staff:
        session.canceled_by = canceled_by_staff
    session.save()
    return session

def get_session_statistics(group, year, month):
    """
    Получает статистику по сессиям за месяц
    """
    sessions = get_sessions_for_month(group, year, month)
    
    total_sessions = sessions.count()
    closed_sessions = sessions.filter(is_closed=True).count()
    canceled_sessions = sessions.filter(is_canceled=True).count()
    active_sessions = 0
    future_sessions = 0
    past_sessions = 0
    
    current_time = timezone.now()
    
    for session in sessions:
        state = get_session_state(session, current_time)
        if state == 'active':
            active_sessions += 1
        elif state == 'future':
            future_sessions += 1
        elif state == 'past':
            past_sessions += 1
    
    return {
        'total': total_sessions,
        'closed': closed_sessions,
        'canceled': canceled_sessions,
        'active': active_sessions,
        'future': future_sessions,
        'past': past_sessions
    }

def auto_ensure_yearly_schedule(group):
    """
    Автоматически обеспечивает наличие расписания до конца текущего года
    И создает расписание на следующий год если нужно
    Вызывается при каждом обращении к журналу
    """
    # Ключ кеша на 24 часа, чтобы не дергать генерацию на каждом GET
    cache_key = f"auto_sessions_created_group_{group.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    today = timezone.localdate()
    created_sessions = 0

    # Быстрая проверка: если в текущем месяце есть хотя бы одна сессия —
    # пропускаем тяжелые проверки конца года
    month_has_any = TrainingSession.objects.filter(
        training_group=group, date__year=today.year, date__month=today.month
    ).exists()

    if not month_has_any:
        # 1. Проверяем и создаем сессии до конца текущего года
        december_sessions = TrainingSession.objects.filter(
            training_group=group,
            date__year=today.year,
            date__month=12
        ).exists()
        if not december_sessions:
            created_sessions += ensure_yearly_sessions_for_group(group, today)

    # 2. Если мы во втором полугодии, создаем сессии на следующий год
    if today.month >= 7:
        next_year = today.year + 1
        next_year_sessions = TrainingSession.objects.filter(
            training_group=group,
            date__year=next_year
        ).exists()
        if not next_year_sessions:
            next_year_start = date(next_year, 1, 1)
            created_sessions += ensure_yearly_sessions_for_group(group, next_year_start)

    # 3. В первом квартале убеждаемся, что есть сессии хотя бы на полгода вперед
    if today.month <= 3:
        current_year_sessions = TrainingSession.objects.filter(
            training_group=group,
            date__year=today.year,
            date__month__gte=6
        ).exists()
        if not current_year_sessions:
            created_sessions += ensure_yearly_sessions_for_group(group, today)

    # Кешируем результат на сутки
    cache.set(cache_key, created_sessions, 60 * 60 * 24)
    return created_sessions

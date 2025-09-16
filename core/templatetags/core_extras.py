from django import template

# CLEANUP: remove unused imports; keep filters behavior unchanged

register = template.Library()

@register.filter
def filter_attendance(attendances, date):
    """Фильтр для получения записи посещаемости по дате"""
    try:
        return attendances.filter(date=date).first()
    except Exception:  # CLEANUP: avoid bare except
        return None

@register.filter
def get_payment(payments, athlete):
    """Фильтр для получения записи оплаты для спортсмена"""
    try:
        return payments.filter(athlete=athlete).first()
    except Exception:  # CLEANUP: avoid bare except
        return None

@register.filter
def filter_paid(payments):
    """Фильтр для получения полностью оплаченных записей"""
    try:
        return payments.filter(status='paid')
    except Exception:  # CLEANUP: avoid bare except
        return payments.none()

@register.filter
def filter_partial(payments):
    """Фильтр для получения частично оплаченных записей"""
    try:
        return payments.filter(status='partial')
    except Exception:  # CLEANUP: avoid bare except
        return payments.none()

@register.filter
def filter_unpaid(payments):
    """Фильтр для получения неоплаченных записей"""
    try:
        return payments.filter(status='unpaid')
    except Exception:  # CLEANUP: avoid bare except
        return payments.none() 
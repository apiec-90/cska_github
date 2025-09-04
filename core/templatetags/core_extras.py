from django import template
from attendance.models import Attendance
from payments.models import Payment

register = template.Library()

@register.filter
def filter_attendance(attendances, date):
    """Фильтр для получения записи посещаемости по дате"""
    try:
        return attendances.filter(date=date).first()
    except:
        return None

@register.filter
def get_payment(payments, athlete):
    """Фильтр для получения записи оплаты для спортсмена"""
    try:
        return payments.filter(athlete=athlete).first()
    except:
        return None

@register.filter
def filter_paid(payments):
    """Фильтр для получения полностью оплаченных записей"""
    try:
        return payments.filter(status='paid')
    except:
        return payments.none()

@register.filter
def filter_partial(payments):
    """Фильтр для получения частично оплаченных записей"""
    try:
        return payments.filter(status='partial')
    except:
        return payments.none()

@register.filter
def filter_unpaid(payments):
    """Фильтр для получения неоплаченных записей"""
    try:
        return payments.filter(status='unpaid')
    except:
        return payments.none() 
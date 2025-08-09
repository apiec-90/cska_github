"""
Кастомные виджеты для форм
"""
from django import forms
from django.forms.widgets import CheckboxSelectMultiple


class WeekdayToggleWidget(CheckboxSelectMultiple):
    """
    Кастомный виджет для выбора дней недели с toggle-переключателями
    """
    template_name = 'admin/widgets/weekday_toggle.html'
    
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update({
            'class': 'weekday-toggle-widget'
        })
        super().__init__(attrs)
    
    class Media:
        css = {
            'all': ('admin/css/toggle.css',)
        }

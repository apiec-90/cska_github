from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home(request):
    """Главная страница приложения"""
    context = {
        'title': 'Главная - SportCRM',
        'stats': {
            'groups': 5,  # Будет заменено на реальные данные
            'athletes': 25,
            'attendance_today': 18,
            'payments_pending': 3,
        }
    }
    return render(request, 'core/home.html', context)


@login_required
def dashboard(request):
    """Дашборд с аналитикой"""
    context = {
        'title': 'Дашборд - SportCRM',
    }
    return render(request, 'core/dashboard.html', context) 
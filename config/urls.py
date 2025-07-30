"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.conf.urls.static import static
from . import views
import datetime

# Health check view для проверки работы сервера
def health_check(request):
    """Endpoint для проверки состояния сервера"""
    try:
        # Проверяем подключение к базе данных
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return JsonResponse({
        'status': 'ok',
        'timestamp': datetime.datetime.now().isoformat(),
        'database': db_status,
        'message': 'Server is running'
    })

# Простой ping endpoint
def ping(request):
    """Простой ping endpoint"""
    return JsonResponse({'ping': 'pong'})

urlpatterns = [
    path('', views.home, name='home'),  # Главная страница
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),  # Полная проверка сервера
    path('ping/', ping, name='ping'),  # Простая проверка доступности
]

# Добавляем маршруты для статических файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Добавляем django-browser-reload для автообновления
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

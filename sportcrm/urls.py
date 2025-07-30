"""
Конфигурация URL для проекта SportCRM.

Список `urlpatterns` направляет URL к представлениям. Для получения дополнительной информации см.:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns  # Для интернационализации URL

# URL без префикса языка
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # Для переключения языков
]

# URL с префиксом языка
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    prefix_default_language=False,  # Не добавлять префикс для языка по умолчанию
)

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

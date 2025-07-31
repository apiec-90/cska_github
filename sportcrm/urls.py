"""
Конфигурация URL для проекта SportCRM.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns

# URL без префикса языка
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

# URL с префиксом языка
urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

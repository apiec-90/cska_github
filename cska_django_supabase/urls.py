"""
URL configuration for cska_django_supabase project.

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
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    start_registration,
    step2_view,
    step3_view,
    step4_view,
    cancel_registration,
    finish_registration,
)

urlpatterns = [
    path('admin/', admin.site.urls),  # Только админка для суперпользователей
    path('register/', start_registration, name='start_registration'),
    path('register/step2/<int:draft_id>/', step2_view, name='register_step2'),
    path('register/step3/<int:draft_id>/', step3_view, name='register_step3'),
    path('register/step4/<int:draft_id>/', step4_view, name='register_step4'),
    path('register/cancel/', cancel_registration, name='cancel_registration'),
    path('register/done/', finish_registration, name='register_done'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

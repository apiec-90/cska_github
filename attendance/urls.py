from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.list_attendance, name='list'),
    path('create/', views.create_attendance, name='create'),
    path('<int:pk>/', views.attendance_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_attendance, name='edit'),
    path('<int:pk>/delete/', views.delete_attendance, name='delete'),
] 
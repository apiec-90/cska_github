from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.list_groups, name='list'),
    path('create/', views.create_group, name='create'),
    path('<int:pk>/', views.group_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_group, name='edit'),
    path('<int:pk>/delete/', views.delete_group, name='delete'),
] 
from django.urls import path
from . import views

app_name = 'athletes'

urlpatterns = [
    path('', views.list_athletes, name='list'),
    path('create/', views.create_athlete, name='create'),
    path('<int:pk>/', views.athlete_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_athlete, name='edit'),
    path('<int:pk>/delete/', views.delete_athlete, name='delete'),
] 
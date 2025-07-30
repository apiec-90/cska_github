from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.list_payments, name='list'),
    path('create/', views.create_payment, name='create'),
    path('<int:pk>/', views.payment_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_payment, name='edit'),
    path('<int:pk>/delete/', views.delete_payment, name='delete'),
] 
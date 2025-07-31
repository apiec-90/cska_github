from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('ping/', views.ping, name='ping'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('athletes/<int:athlete_id>/', views.athlete_detail, name='athlete_detail'),
    
    path('attendance/', views.attendance_journal, name='attendance_journal'),
    path('attendance/update/', views.update_attendance, name='update_attendance'),
    path('attendance/export/excel/', views.export_attendance_excel, name='export_attendance_excel'),
    
    path('payments/', views.payments_view, name='payments_view'),
    path('payments/update/', views.update_payment, name='update_payment'),
    path('payments/export/excel/', views.export_payments_excel, name='export_payments_excel'),
] 
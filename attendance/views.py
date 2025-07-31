from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Attendance

def list_attendance(request):
    """Список посещаемости"""
    attendance_records = Attendance.objects.all().order_by('-date', 'athlete__last_name')
    context = {
        'title': 'Посещаемость',
        'attendance_records': attendance_records,
    }
    return render(request, 'attendance/list.html', context)

@login_required
def create_attendance(request):
    """Создание записи о посещаемости"""
    context = {
        'title': 'Отметить посещаемость',
    }
    return render(request, 'attendance/create.html', context)

@login_required
def attendance_detail(request, pk):
    """Детальная информация о посещаемости"""
    attendance = get_object_or_404(Attendance, pk=pk)
    context = {
        'title': 'Детали посещаемости',
        'attendance': attendance,
    }
    return render(request, 'attendance/detail.html', context)

@login_required
def edit_attendance(request, pk):
    """Редактирование записи о посещаемости"""
    attendance = get_object_or_404(Attendance, pk=pk)
    context = {
        'title': 'Редактировать посещаемость',
        'attendance': attendance,
    }
    return render(request, 'attendance/edit.html', context)

@login_required
def delete_attendance(request, pk):
    """Удаление записи о посещаемости"""
    attendance = get_object_or_404(Attendance, pk=pk)
    attendance.delete()
    messages.success(request, 'Запись о посещаемости успешно удалена')
    return redirect('attendance:list')

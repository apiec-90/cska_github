from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def list_attendance(request):
    """Список посещаемости"""
    context = {
        'title': 'Посещаемость',
        'attendance_records': [],  # Будет заменено на реальные данные
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
    context = {
        'title': 'Детали посещаемости',
        'attendance': None,  # Будет заменено на реальные данные
    }
    return render(request, 'attendance/detail.html', context)


@login_required
def edit_attendance(request, pk):
    """Редактирование записи о посещаемости"""
    context = {
        'title': 'Редактировать посещаемость',
        'attendance': None,  # Будет заменено на реальные данные
    }
    return render(request, 'attendance/edit.html', context)


@login_required
def delete_attendance(request, pk):
    """Удаление записи о посещаемости"""
    messages.success(request, 'Запись о посещаемости успешно удалена')
    return redirect('attendance:list')

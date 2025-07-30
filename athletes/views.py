from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def list_athletes(request):
    """Список спортсменов"""
    context = {
        'title': 'Спортсмены',
        'athletes': [],  # Будет заменено на реальные данные
    }
    return render(request, 'athletes/list.html', context)


@login_required
def create_athlete(request):
    """Создание нового спортсмена"""
    context = {
        'title': 'Добавить спортсмена',
    }
    return render(request, 'athletes/create.html', context)


@login_required
def athlete_detail(request, pk):
    """Детальная информация о спортсмене"""
    context = {
        'title': 'Детали спортсмена',
        'athlete': None,  # Будет заменено на реальные данные
    }
    return render(request, 'athletes/detail.html', context)


@login_required
def edit_athlete(request, pk):
    """Редактирование спортсмена"""
    context = {
        'title': 'Редактировать спортсмена',
        'athlete': None,  # Будет заменено на реальные данные
    }
    return render(request, 'athletes/edit.html', context)


@login_required
def delete_athlete(request, pk):
    """Удаление спортсмена"""
    messages.success(request, 'Спортсмен успешно удален')
    return redirect('athletes:list')

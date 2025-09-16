from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Athlete

def list_athletes(request):
    """Список спортсменов"""
    # N+1 safe: fetch related user once
    athletes = (
        Athlete.objects.filter(is_active=True)
        .select_related('user')
        .order_by('last_name', 'first_name')
    )
    context = {
        'title': 'Спортсмены',
        'athletes': athletes,
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
    athlete = get_object_or_404(Athlete, pk=pk, is_active=True)
    context = {
        'title': 'Детали спортсмена',
        'athlete': athlete,
    }
    return render(request, 'athletes/detail.html', context)

@login_required
def edit_athlete(request, pk):
    """Редактирование спортсмена"""
    athlete = get_object_or_404(Athlete, pk=pk, is_active=True)
    context = {
        'title': 'Редактировать спортсмена',
        'athlete': athlete,
    }
    return render(request, 'athletes/edit.html', context)

@login_required
def delete_athlete(request, pk):
    """Удаление спортсмена"""
    athlete = get_object_or_404(Athlete, pk=pk, is_active=True)
    athlete.is_active = False
    athlete.save()
    messages.success(request, 'Спортсмен успешно удален')
    return redirect('athletes:list')

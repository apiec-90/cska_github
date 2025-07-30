from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def list_groups(request):
    """Список спортивных групп"""
    context = {
        'title': 'Спортивные группы',
        'groups': [],  # Будет заменено на реальные данные
    }
    return render(request, 'groups/list.html', context)


@login_required
def create_group(request):
    """Создание новой группы"""
    context = {
        'title': 'Создать группу',
    }
    return render(request, 'groups/create.html', context)


@login_required
def group_detail(request, pk):
    """Детальная информация о группе"""
    context = {
        'title': 'Детали группы',
        'group': None,  # Будет заменено на реальные данные
    }
    return render(request, 'groups/detail.html', context)


@login_required
def edit_group(request, pk):
    """Редактирование группы"""
    context = {
        'title': 'Редактировать группу',
        'group': None,  # Будет заменено на реальные данные
    }
    return render(request, 'groups/edit.html', context)


@login_required
def delete_group(request, pk):
    """Удаление группы"""
    messages.success(request, 'Группа успешно удалена')
    return redirect('groups:list')

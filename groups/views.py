from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Group

def list_groups(request):
    """Список спортивных групп"""
    groups = Group.objects.filter(is_active=True).order_by('number')
    context = {
        'title': 'Спортивные группы',
        'groups': groups,
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
    group = get_object_or_404(Group, pk=pk, is_active=True)
    context = {
        'title': 'Детали группы',
        'group': group,
    }
    return render(request, 'groups/detail.html', context)

@login_required
def edit_group(request, pk):
    """Редактирование группы"""
    group = get_object_or_404(Group, pk=pk, is_active=True)
    context = {
        'title': 'Редактировать группу',
        'group': group,
    }
    return render(request, 'groups/edit.html', context)

@login_required
def delete_group(request, pk):
    """Удаление группы"""
    group = get_object_or_404(Group, pk=pk, is_active=True)
    group.is_active = False
    group.save()
    messages.success(request, 'Группа успешно удалена')
    return redirect('groups:list')

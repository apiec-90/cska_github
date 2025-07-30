from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def list_payments(request):
    """Список оплат"""
    context = {
        'title': 'Оплаты',
        'payments': [],  # Будет заменено на реальные данные
    }
    return render(request, 'payments/list.html', context)


@login_required
def create_payment(request):
    """Создание новой оплаты"""
    context = {
        'title': 'Добавить оплату',
    }
    return render(request, 'payments/create.html', context)


@login_required
def payment_detail(request, pk):
    """Детальная информация об оплате"""
    context = {
        'title': 'Детали оплаты',
        'payment': None,  # Будет заменено на реальные данные
    }
    return render(request, 'payments/detail.html', context)


@login_required
def edit_payment(request, pk):
    """Редактирование оплаты"""
    context = {
        'title': 'Редактировать оплату',
        'payment': None,  # Будет заменено на реальные данные
    }
    return render(request, 'payments/edit.html', context)


@login_required
def delete_payment(request, pk):
    """Удаление оплаты"""
    messages.success(request, 'Оплата успешно удалена')
    return redirect('payments:list')

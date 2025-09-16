from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Payment

def list_payments(request):
    """Список оплат"""
    # N+1 safe: fetch related athlete and user for listing
    payments = (
        Payment.objects.select_related('athlete__user')
        .all()
        .order_by('-month', 'athlete__last_name')
    )
    context = {
        'title': 'Оплаты',
        'payments': payments,
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
    payment = get_object_or_404(Payment.objects.select_related('athlete__user'), pk=pk)
    context = {
        'title': 'Детали оплаты',
        'payment': payment,
    }
    return render(request, 'payments/detail.html', context)

@login_required
def edit_payment(request, pk):
    """Редактирование оплаты"""
    payment = get_object_or_404(Payment.objects.select_related('athlete__user'), pk=pk)
    context = {
        'title': 'Редактировать оплату',
        'payment': payment,
    }
    return render(request, 'payments/edit.html', context)

@login_required
def delete_payment(request, pk):
    """Удаление оплаты"""
    payment = get_object_or_404(Payment, pk=pk)
    payment.delete()
    messages.success(request, 'Оплата успешно удалена')
    return redirect('payments:list')

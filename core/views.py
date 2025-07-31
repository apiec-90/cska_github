from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, date
from calendar import monthrange
import pandas as pd
import tempfile
import os

from groups.models import Group
from athletes.models import Athlete
from attendance.models import Attendance
from payments.models import Payment

def home(request):
    """Главная страница со списком групп"""
    # Получаем активные группы, сортируем по номеру
    groups = Group.objects.filter(is_active=True).order_by('number')  # type: ignore[attr-defined]
    
    context = {
        'groups': groups,
        'total_athletes': Athlete.objects.filter(is_active=True).count(),  # type: ignore[attr-defined]
        'total_groups': groups.count(),
    }
    
    return render(request, 'core/home.html', context)

def ping(request):
    """HTMX тест для проверки сервера"""
    return JsonResponse({
        'status': 'success',
        'message': 'Сервер работает! 🚀'
    })

def group_list(request):
    """Список групп для HTMX"""
    groups = Group.objects.filter(is_active=True).order_by('number')  # type: ignore[attr-defined]
    return render(request, 'groups/group_list.html', {'groups': groups})

def group_detail(request, group_id):
    """Детальная страница группы со спортсменами"""
    group = get_object_or_404(Group, id=group_id, is_active=True)
    athletes = group.athletes.filter(is_active=True).order_by('last_name', 'first_name')
    
    context = {
        'group': group,
        'athletes': athletes,
    }
    
    return render(request, 'groups/group_detail.html', context)

def athlete_detail(request, athlete_id):
    """Личная карточка спортсмена"""
    athlete = get_object_or_404(Athlete, id=athlete_id, is_active=True)
    
    context = {
        'athlete': athlete,
        'documents': athlete.documents.all(),
    }
    
    return render(request, 'athletes/athlete_detail.html', context)

def attendance_journal(request):
    """Журнал посещаемости"""
    groups = Group.objects.filter(is_active=True).order_by('number')  # type: ignore[attr-defined]
    selected_group_id = request.GET.get('group')
    selected_month = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    
    context = {
        'groups': groups,
        'selected_group_id': selected_group_id,
        'selected_month': selected_month,
    }
    
    if selected_group_id:
        group = get_object_or_404(Group, id=selected_group_id)
        athletes = group.athletes.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Получаем дни месяца
        year, month = map(int, selected_month.split('-'))
        _, days_in_month = monthrange(year, month)
        
        # Получаем дни недели группы
        group_days = group.days
        day_names = dict(group.DAYS_CHOICES)
        
        # Создаем календарь для месяца
        calendar_days = []
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            weekday = current_date.strftime('%a').lower()[:3]
            if weekday in group_days:
                calendar_days.append({
                    'date': current_date,
                    'day': day,
                    'weekday': day_names.get(weekday, weekday)
                })
        
        context.update({
            'group': group,
            'athletes': athletes,
            'calendar_days': calendar_days,
            'year': year,
            'month': month,
        })
    
    return render(request, 'attendance/journal.html', context)

def update_attendance(request):
    """Обновление посещаемости через HTMX"""
    if request.method == 'POST':
        # Получаем данные из POST запроса
        athlete_id = request.POST.get('athlete_id')
        attendance_date = request.POST.get('date')
        status = request.POST.get('status')
        
        try:
            # Находим спортсмена и парсим дату
            athlete = Athlete.objects.get(id=athlete_id)  # type: ignore[attr-defined]
            attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
            
            # Создаем или обновляем запись посещаемости
            attendance, created = Attendance.objects.get_or_create(  # type: ignore[attr-defined]
                athlete=athlete,
                date=attendance_date,
                defaults={'status': status}
            )
            
            # Если запись уже существовала, обновляем статус
            if not created:
                attendance.status = status
                attendance.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Посещаемость обновлена'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Неверный метод'}, status=405)

def export_attendance_excel(request):
    """Экспорт посещаемости в Excel"""
    # Получаем параметры из запроса
    group_id = request.GET.get('group')
    month = request.GET.get('month')
    
    # Проверяем наличие обязательных параметров
    if not group_id or not month:
        return JsonResponse({'error': 'Не указаны группа или месяц'}, status=400)
    
    # Находим группу и спортсменов
    group = get_object_or_404(Group, id=group_id)
    athletes = group.athletes.filter(is_active=True).order_by('last_name', 'first_name')
    
    # Парсим год и месяц
    year, month_num = map(int, month.split('-'))
    _, days_in_month = monthrange(year, month_num)
    
    # Создаем DataFrame для Excel
    data = []
    for athlete in athletes:
        # Базовая информация о спортсмене
        row = {
            'ФИО': athlete.full_name,
            'Возраст': f"{athlete.age} лет",
            'Группа': f"Группа {group.number}"
        }
        
        # Добавляем данные посещаемости по дням месяца
        for day in range(1, days_in_month + 1):
            current_date = date(year, month_num, day)
            attendance = Attendance.objects.filter(  # type: ignore[attr-defined]
                athlete=athlete,
                date=current_date
            ).first()
            
            # Статус посещаемости: ✓ - присутствовал, ✗ - отсутствовал
            status = '✓' if attendance and attendance.status == 'present' else '✗'
            row[f'{day}'] = status
        
        data.append(row)
    
    # Создаем pandas DataFrame из данных
    df = pd.DataFrame(data)
    
    # Создаем временный файл для Excel
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        # Записываем DataFrame в Excel файл
        with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Посещаемость', index=False)
        
        # Читаем содержимое файла
        with open(tmp_file.name, 'rb') as f:
            excel_data = f.read()
        
        # Удаляем временный файл
        os.unlink(tmp_file.name)
    
    # Создаем HTTP ответ с Excel файлом
    response = HttpResponse(
        excel_data,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=attendance_{group.number}_{month}.xlsx'
    
    return response

def payments_view(request):
    """Система оплаты"""
    groups = Group.objects.filter(is_active=True).order_by('number')  # type: ignore[attr-defined]
    selected_group_id = request.GET.get('group')
    selected_month = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    
    context = {
        'groups': groups,
        'selected_group_id': selected_group_id,
        'selected_month': selected_month,
    }
    
    if selected_group_id:
        group = get_object_or_404(Group, id=selected_group_id)
        athletes = group.athletes.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Получаем месяц для оплаты
        year, month = map(int, selected_month.split('-'))
        payment_month = date(year, month, 1)
        
        # Получаем или создаем записи оплаты
        payments = []
        for athlete in athletes:
            payment, created = Payment.objects.get_or_create(  # type: ignore[attr-defined]
                athlete=athlete,
                month=payment_month,
                defaults={'amount': 5000.00}
            )
            payments.append(payment)
        
        context.update({
            'group': group,
            'athletes': athletes,
            'payments': payments,
            'payment_month': payment_month,
        })
    
    return render(request, 'payments/payments.html', context)

def update_payment(request):
    """Обновление статуса оплаты через HTMX"""
    if request.method == 'POST':
        athlete_id = request.POST.get('athlete_id')
        month = request.POST.get('month')
        paid_amount = request.POST.get('paid_amount', 0)
        
        try:
            athlete = Athlete.objects.get(id=athlete_id)  # type: ignore[attr-defined]
            payment_month = datetime.strptime(month, '%Y-%m-%d').date()
            
            payment, created = Payment.objects.get_or_create(  # type: ignore[attr-defined]
                athlete=athlete,
                month=payment_month,
                defaults={'amount': 5000.00}
            )
            
            payment.paid_amount = float(paid_amount)
            payment.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Оплата обновлена',
                'payment_status': payment.status,
                'row_color': payment.row_color
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Неверный метод'}, status=405)

def export_payments_excel(request):
    """Экспорт оплаты в Excel"""
    group_id = request.GET.get('group')
    month = request.GET.get('month')
    
    if not group_id or not month:
        return JsonResponse({'error': 'Не указаны группа или месяц'}, status=400)
    
    group = get_object_or_404(Group, id=group_id)
    athletes = group.athletes.filter(is_active=True).order_by('last_name', 'first_name')
    
    year, month_num = map(int, month.split('-'))
    payment_month = date(year, month_num, 1)
    
    # Создаем DataFrame
    data = []
    for athlete in athletes:
        payment = Payment.objects.filter(  # type: ignore[attr-defined]
            athlete=athlete,
            month=payment_month
        ).first()
        
        if payment:
            data.append({
                'ФИО': athlete.full_name,
                'Возраст': f"{athlete.age} лет",
                'Группа': f"Группа {group.number}",
                'Сумма к оплате': payment.amount,
                'Оплачено': payment.paid_amount,
                'Остаток': payment.remaining_amount,
                'Статус': payment.get_status_display(),
                'Дата оплаты': payment.payment_date.strftime('%d.%m.%Y') if payment.payment_date else '-'
            })
    
    df = pd.DataFrame(data)
    
    # Создаем временный файл для Excel
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        # Записываем DataFrame в Excel файл
        with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Оплата', index=False)
        
        # Читаем содержимое файла
        with open(tmp_file.name, 'rb') as f:
            excel_data = f.read()
        
        # Удаляем временный файл
        os.unlink(tmp_file.name)
    
    # Создаем HTTP ответ с Excel файлом
    response = HttpResponse(
        excel_data,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=payments_{group.number}_{month}.xlsx'
    
    return response 
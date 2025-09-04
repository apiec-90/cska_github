<<<<<<< HEAD
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import (
    AthleteForm,
    ParentForm,
    Step1UserForm,
    Step2RoleForm,
    TrainerForm,
    CommonProfileForm,
    StaffSubroleForm,
)
from .models import Athlete, Parent, RegistrationDraft, Trainer, Staff
from . import utils


def _cleanup_existing_draft(request: HttpRequest) -> None:
    """Удалить незавершенный черновик текущего инициатора регистрации.
    Хранит строго одну активную попытку.
    """
    draft_id = request.session.get("draft_id")
    if draft_id:
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
            draft.safe_dispose()
        except RegistrationDraft.DoesNotExist:
            pass
        request.session.pop("draft_id", None)

    # Также подчистим другие незавершенные драфты, созданные этим пользователем ранее
    if request.user.is_authenticated:
        for d in RegistrationDraft.objects.filter(created_by=request.user, is_completed=False):
            d.safe_dispose()


@require_http_methods(["GET", "POST"])
def start_registration(request: HttpRequest) -> HttpResponse:
    """Шаг 1: Создание временного пользователя и черновика регистрации.
    В любой заход сюда удаляем любые старые незавершенные драфты.
    """
    _cleanup_existing_draft(request)

    if request.method == "POST":
        form = Step1UserForm(request.POST)
        if form.is_valid():
            temp_user: User = form.save(commit=False)
            temp_user.is_active = False
            temp_user.save()

            draft = RegistrationDraft.objects.create(
                user=temp_user,
                created_by=request.user if request.user.is_authenticated else temp_user,
                current_step=1,
                is_completed=False,
            )
            request.session["draft_id"] = draft.id
            return redirect("register_step2", draft_id=draft.id)
    else:
        form = Step1UserForm()

    return render(request, "register/step1.html", {"form": form})


@require_http_methods(["GET", "POST"])
def step2_view(request: HttpRequest, draft_id: int) -> HttpResponse:
    draft = get_object_or_404(RegistrationDraft, pk=draft_id, is_completed=False)
    if request.session.get("draft_id") != draft.id:
        # защита от чужих/устаревших попыток
        _cleanup_existing_draft(request)
        request.session["draft_id"] = draft.id

    if request.method == "POST":
        form = Step2RoleForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data["role"]
            draft.role = role
            draft.current_step = 2
            draft.save(update_fields=["role", "current_step", "updated_at"])
            
            # Назначаем базовую группу по роли
            utils.assign_groups_for_registration(draft.user, role)
            
            return redirect("register_step3", draft_id=draft.id)
    else:
        initial = {"role": draft.role} if draft.role else None
        form = Step2RoleForm(initial=initial)

    return render(request, "register/step2.html", {"form": form, "draft": draft})


@require_http_methods(["GET", "POST"])
def step3_view(request: HttpRequest, draft_id: int) -> HttpResponse:
    draft = get_object_or_404(RegistrationDraft, pk=draft_id, is_completed=False)
    if not draft.role:
        return redirect("register_step2", draft_id=draft.id)

    if request.method == "POST":
        form = CommonProfileForm(request.POST)
        if form.is_valid():
            # Сохраняем ФИО в User
            draft.user.first_name = form.cleaned_data['first_name']
            draft.user.last_name = form.cleaned_data['last_name']
            draft.user.save()
            
            # Создаем профиль в соответствующей модели
            if draft.role == "trainer":
                Trainer.objects.create(
                    user=draft.user,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    phone=form.cleaned_data.get('phone', ''),
                    birth_date=form.cleaned_data['birth_date'],
                )
            elif draft.role == "parent":
                Parent.objects.create(
                    user=draft.user,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    phone=form.cleaned_data.get('phone', ''),
                    birth_date=form.cleaned_data['birth_date'],
                )
            elif draft.role == "athlete":
                Athlete.objects.create(
                    user=draft.user,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    phone=form.cleaned_data.get('phone', ''),
                    birth_date=form.cleaned_data['birth_date'],
                )
            elif draft.role == "staff":
                Staff.objects.create(
                    user=draft.user,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    phone=form.cleaned_data.get('phone', ''),
                    birth_date=form.cleaned_data['birth_date'],
                    role='other',  # Базовая роль, подроль выберем на шаге 4
                )

            draft.current_step = 3
            draft.save(update_fields=["current_step", "updated_at"])
            
            # Для staff идем на выбор подроли, для остальных завершаем
            if draft.role == "staff":
                return redirect("register_step4", draft_id=draft.id)
            else:
                # Активируем пользователя и завершаем
                draft.user.is_active = True
                draft.user.save()
                draft.is_completed = True
                draft.save(update_fields=["is_completed", "updated_at"])
                request.session.pop("draft_id", None)
                return redirect("register_done")
    else:
        form = CommonProfileForm(initial={
            'first_name': draft.user.first_name,
            'last_name': draft.user.last_name,
        })

    return render(request, "register/step3.html", {"form": form, "draft": draft})


@require_http_methods(["GET", "POST"])
def step4_view(request: HttpRequest, draft_id: int) -> HttpResponse:
    """Шаг 4: Выбор подроли для staff"""
    draft = get_object_or_404(RegistrationDraft, pk=draft_id, is_completed=False)
    if draft.role != "staff":
        return redirect("register_done")

    if request.method == "POST":
        form = StaffSubroleForm(request.POST)
        if form.is_valid():
            subrole = form.cleaned_data['subrole']
            
            # Обновляем профиль staff с подролью
            staff = Staff.objects.get(user=draft.user)
            staff.subrole = subrole
            staff.save()
            
            # Назначаем группу подроли
            utils.assign_groups_for_registration(draft.user, 'staff', subrole)
            
            # Активируем пользователя и завершаем
            draft.user.is_active = True
            draft.user.save()
            draft.is_completed = True
            draft.save(update_fields=["is_completed", "updated_at"])
            request.session.pop("draft_id", None)
            return redirect("register_done")
    else:
        form = StaffSubroleForm()

    return render(request, "register/step4.html", {"form": form, "draft": draft})


@require_http_methods(["POST", "GET"])
def cancel_registration(request: HttpRequest) -> HttpResponse:
    draft_id = request.session.get("draft_id")
    if draft_id:
        try:
            draft = RegistrationDraft.objects.get(pk=draft_id, is_completed=False)
            draft.safe_dispose()
        except RegistrationDraft.DoesNotExist:
            pass
        request.session.pop("draft_id", None)

    messages.info(request, "Регистрация отменена и очищена.")
    return redirect("start_registration")


@require_http_methods(["GET"])
def finish_registration(request: HttpRequest) -> HttpResponse:
    # Просто страница успеха
    return render(request, "register/done.html")


=======
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
>>>>>>> bedbb2b1a87a3bede18d794b18be9309c5599d3e

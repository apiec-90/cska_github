from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Trainer, Parent, Athlete, Staff, TrainingGroup, GroupSchedule
from .widgets import WeekdayToggleWidget  # noqa: F401 - used by templates/admin
import logging

# CLEANUP: use logging instead of print for internal notices
logger = logging.getLogger(__name__)


class Step1UserForm(UserCreationForm):
    """Шаг 1: временный пользователь (is_active=False)."""

    email = forms.EmailField(label="Email", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")


class Step2RoleForm(forms.Form):
    ROLE_CHOICES = (
        ("trainer", "Тренер"),
        ("parent", "Родитель"),
        ("athlete", "Спортсмен"),
        ("staff", "Сотрудник"),
    )
    role = forms.ChoiceField(label="Роль", choices=ROLE_CHOICES, required=True)


class CommonProfileForm(forms.Form):
    """Общая форма профиля для всех ролей (шаг 3)"""
    last_name = forms.CharField(label="Фамилия", max_length=150)
    first_name = forms.CharField(label="Имя", max_length=150)
    phone = forms.CharField(label="Телефон", max_length=255, required=False, 
                          widget=forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}))
    birth_date = forms.DateField(label="Дата рождения", widget=forms.DateInput(attrs={'type': 'date'}))


class StaffSubroleForm(forms.Form):
    """Форма выбора подроли для сотрудника (шаг 4)"""
    subrole = forms.ChoiceField(label="Подроль", choices=[
        ('manager', 'Менеджер'),
    ], required=True)


class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ("last_name", "first_name", "phone", "birth_date")
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}),
        }


class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ("last_name", "first_name", "phone", "birth_date")
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}),
        }


class AthleteForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = ("last_name", "first_name", "birth_date", "phone")
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }


class Step3StaffRoleForm(forms.Form):
    """Шаг 3: выбор подроли сотрудника"""

    staff_role = forms.ChoiceField(label="Подроль сотрудника", choices=[], required=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # наполняем из перечисления ролей Staff
        self.fields["staff_role"].choices = Staff.ROLE_CHOICES


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ("role", "subrole", "last_name", "first_name", "phone", "birth_date")
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}),
        }


class StaffRegisterProfileForm(forms.ModelForm):
    """Форма шага 4 (админ) — только профиль сотрудника без роли/подроли"""
    class Meta:
        model = Staff
        fields = ("last_name", "first_name", "phone", "birth_date")
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}),
        }


class GroupScheduleForm(forms.ModelForm):
    """Форма расписания группы с чекбоксами для дней недели"""
    
    WEEKDAY_CHOICES = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
        (7, 'Воскресенье'),
    ]
    
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'weekday-checkboxes'}),
        label="Дни недели",
        help_text="Выберите дни, когда проходят тренировки",
        required=True  # Обязательное поле
    )
    
    class Meta:
        model = GroupSchedule
        fields = ('training_group', 'start_time', 'end_time')
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Извлекаем параметры из GET запроса (для предзаполнения)
        initial = kwargs.get('initial', {})  # noqa: F841 - reserved for future use
        
        super().__init__(*args, **kwargs)
        
        # Переупорядочиваем поля - weekdays должно отображаться после training_group
        field_order = ['training_group', 'weekdays', 'start_time', 'end_time']
        self.order_fields(field_order)
        
        if self.instance.pk:
            # При редактировании показываем все дни для данной группы и времени
            existing_schedules = GroupSchedule.objects.filter(
                training_group=self.instance.training_group,
                start_time=self.instance.start_time,
                end_time=self.instance.end_time
            )
            weekdays = [str(schedule.weekday) for schedule in existing_schedules]
            self.fields['weekdays'].initial = weekdays
    
    def clean_weekdays(self):
        """Валидация выбранных дней недели"""
        weekdays = self.cleaned_data.get('weekdays')
        if not weekdays:
            raise forms.ValidationError("Выберите хотя бы один день недели")
        return weekdays
    
    def save(self, commit=True):
        """Сохраняем отдельные записи для каждого выбранного дня"""
        if not commit:
            # Для commit=False возвращаем несохраненный экземпляр
            return super().save(commit=False)
        
        weekdays = self.cleaned_data.get('weekdays', [])
        training_group = self.cleaned_data.get('training_group')
        start_time = self.cleaned_data.get('start_time')
        end_time = self.cleaned_data.get('end_time')
        
        if not weekdays:
            return None
        
        # Если редактируем существующую запись, удаляем все связанные записи группы с тем же временем
        if self.instance.pk:
            GroupSchedule.objects.filter(
                training_group=self.instance.training_group,
                start_time=self.instance.start_time,
                end_time=self.instance.end_time
            ).delete()
        
        # Создаем новые записи для каждого выбранного дня
        created_instances = []
        for weekday in weekdays:
            # Проверяем, не существует ли уже такая запись
            existing = GroupSchedule.objects.filter(
                training_group=training_group,
                weekday=int(weekday),
                start_time=start_time
            ).first()
            
            if existing:
                # Обновляем существующую запись
                existing.end_time = end_time
                existing.save()
                created_instances.append(existing)
            else:
                # Создаем новую запись
                instance = GroupSchedule.objects.create(
                    training_group=training_group,
                    weekday=int(weekday),
                    start_time=start_time,
                    end_time=end_time
                )
                created_instances.append(instance)
        
        # Автоматически создаем тренировочные сессии на месяц
        if created_instances:
            self._generate_training_sessions(training_group)
        
        # Возвращаем первую созданную запись для совместимости с Django Admin
        return created_instances[0] if created_instances else None
    
    def _generate_training_sessions(self, training_group):
        """Автоматическое создание тренировочных сессий на месяц"""
        from django.utils import timezone
        from datetime import timedelta, date
        from core.models import TrainingSession
        
        today = timezone.localdate()
        
        # Генерируем сессии на текущий и следующий месяц
        for months_ahead in [0, 1]:
            if months_ahead == 0:
                # Текущий месяц (с сегодняшнего дня)
                first_day = today
                if today.month == 12:
                    next_first = today.replace(year=today.year+1, month=1, day=1)
                else:
                    next_first = today.replace(month=today.month+1, day=1)
            else:
                # Следующий месяц
                year = today.year
                month = today.month + months_ahead
                while month > 12:
                    year += 1
                    month -= 12
                
                first_day = date(year, month, 1)
                if month == 12:
                    next_first = date(year+1, 1, 1)
                else:
                    next_first = date(year, month+1, 1)
            
            # Получаем актуальное расписание группы
            from core.models import GroupSchedule
            schedules = GroupSchedule.objects.filter(training_group=training_group)
            
            created_count = 0
            current_date = first_day
            while current_date < next_first:
                for schedule in schedules:
                    # weekday в модели: 1=Пн, 2=Вт, ..., 7=Вс
                    # weekday() в Python: 0=Пн, 1=Вт, ..., 6=Вс
                    if current_date.weekday() + 1 == schedule.weekday:
                        # Проверяем, существует ли уже сессия
                        existing_session = TrainingSession.objects.filter(
                            training_group=training_group,
                            date=current_date,
                            start_time=schedule.start_time
                        ).exists()
                        
                        if not existing_session:
                            # Создаем новую сессию
                            TrainingSession.objects.create(
                                training_group=training_group,
                                date=current_date,
                                start_time=schedule.start_time,
                                end_time=schedule.end_time,
                                is_closed=False,
                                is_canceled=False
                            )
                            created_count += 1
                
                current_date += timedelta(days=1)
            
            if created_count > 0:
                logger.info(
                    # CLEANUP: internal info message instead of stdout print
                    f"CLEANUP: авто-создано {created_count} тренировочных сессий для группы {training_group} на {months_ahead+1}-й месяц"
                )


# ===== Новые формы для расширенного шага 3 (профили) =====
class AthleteProfileForm(forms.Form):
    # # ФИО сохраняем в User, дата рождения пойдет в Athlete
    last_name = forms.CharField(label="Фамилия", max_length=150)
    first_name = forms.CharField(label="Имя", max_length=150)
    birth_date = forms.DateField(label="Дата рождения", widget=forms.DateInput(attrs={'type': 'date'}))
    phone = forms.CharField(label="Телефон", max_length=255, required=True)


class ParentProfileForm(forms.Form):
    last_name = forms.CharField(label="Фамилия", max_length=150)
    first_name = forms.CharField(label="Имя", max_length=150)
    phone = forms.CharField(label="Телефон", max_length=255, required=True)


# ===== Новые формы для расширенного шага 4 (связи) =====
class AthleteRelationsForm(forms.Form):
    groups = forms.ModelMultipleChoiceField(
        label="Группы",
        queryset=TrainingGroup.objects.filter(is_active=True),
        required=True,
        widget=forms.SelectMultiple
    )


class ParentRelationsForm(forms.Form):
    children = forms.ModelMultipleChoiceField(
        label="Дети (спортсмены)",
        queryset=Athlete.objects.all(),
        required=False,
        widget=forms.SelectMultiple
    )


class TrainerRelationsForm(forms.Form):
    groups = forms.ModelMultipleChoiceField(
        label="Группы тренера",
        queryset=TrainingGroup.objects.filter(trainer__isnull=True),
        required=False,
        widget=forms.SelectMultiple
    )


class AthleteAdminForm(forms.ModelForm):
    # Поля User для редактирования в форме спортсмена
    user_last_name = forms.CharField(label="Фамилия", max_length=150, required=False)
    user_first_name = forms.CharField(label="Имя", max_length=150, required=False)

    class Meta:
        model = Athlete
        fields = ("user_last_name", "user_first_name", "birth_date", "phone")
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Инициализируем из связанного пользователя
        if self.instance and getattr(self.instance, 'user_id', None):
            self.fields['user_last_name'].initial = self.instance.user.last_name
            self.fields['user_first_name'].initial = self.instance.user.first_name

    def save(self, commit=True):
        athlete = super().save(commit=False)
        # Сохраняем ФИО в связанного пользователя
        if athlete.user_id:
            athlete.user.last_name = self.cleaned_data.get('user_last_name', '')
            athlete.user.first_name = self.cleaned_data.get('user_first_name', '')
            athlete.user.save(update_fields=['last_name', 'first_name'])
        if commit:
            athlete.save()
        return athlete


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Trainer, Parent, Athlete, Staff, TrainingGroup


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
        fields = ("phone", "birth_date")


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


# ===== Новые формы для расширенного шага 3 (профили) =====
class AthleteProfileForm(forms.Form):
    # # ФИО сохраняем в User, дата рождения пойдет в Athlete
    last_name = forms.CharField(label="Фамилия", max_length=150)
    first_name = forms.CharField(label="Имя", max_length=150)
    birth_date = forms.DateField(label="Дата рождения", widget=forms.DateInput(attrs={'type': 'date'}))
    phone = forms.CharField(label="Телефон", max_length=255, required=False)


class ParentProfileForm(forms.Form):
    last_name = forms.CharField(label="Фамилия", max_length=150)
    first_name = forms.CharField(label="Имя", max_length=150)
    phone = forms.CharField(label="Телефон", max_length=255, required=False)


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


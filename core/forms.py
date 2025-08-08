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


class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ("specialization", "experience_years", "certification", "phone", "birth_date")
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}),
        }


class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ("phone",)


class AthleteForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = ("birth_date", "phone")
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
        fields = ("role", "description", "phone", "birth_date")
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}),
            'description': forms.Textarea(attrs={'rows': 3}),
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


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Trainer, Parent, Athlete


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
        fields = ()  # у родителя дополнительных обязательных полей нет


class AthleteForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = ("birth_date",)
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }



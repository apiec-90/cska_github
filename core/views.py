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
)
from .models import Athlete, Parent, RegistrationDraft, Trainer


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
            draft.role = form.cleaned_data["role"]
            draft.current_step = 2
            draft.save(update_fields=["role", "current_step", "updated_at"])
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

    form_cls = {
        "trainer": TrainerForm,
        "parent": ParentForm,
        "athlete": AthleteForm,
    }[draft.role]

    instance = None
    if draft.role == "trainer":
        instance = Trainer.objects.filter(user=draft.user).first()
    elif draft.role == "parent":
        instance = Parent.objects.filter(user=draft.user).first()
    elif draft.role == "athlete":
        instance = Athlete.objects.filter(user=draft.user).first()

    if request.method == "POST":
        form = form_cls(request.POST, instance=instance)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = draft.user
            profile.save()

            draft.current_step = 3
            draft.is_completed = True
            draft.save(update_fields=["current_step", "is_completed", "updated_at"])

            # активируем пользователя
            draft.user.is_active = True
            draft.user.save(update_fields=["is_active"])

            request.session.pop("draft_id", None)
            return redirect("register_done")
    else:
        form = form_cls(instance=instance)

    return render(request, "register/step3.html", {"form": form, "draft": draft})


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



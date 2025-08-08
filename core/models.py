from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone

class PaymentMethod(models.Model):
    """Способ оплаты"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, verbose_name="Название")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        db_table = 'payment_method'
        verbose_name = "Способ оплаты"
        verbose_name_plural = "Способы оплаты"

    def __str__(self):
        return self.name

class Trainer(models.Model):
    """Тренер"""
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    phone = models.CharField(max_length=255, unique=True, verbose_name="Телефон")
    birth_date = models.DateField(verbose_name="Дата рождения")
    # Новые поля ФИО на профиль тренера
    first_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="Фамилия")
    is_archived = models.BooleanField(default=False, verbose_name="Архивирован")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивирования")
    archived_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Архивирован кем")

    class Meta:
        db_table = 'trainer'
        verbose_name = "Тренер"
        verbose_name_plural = "Тренеры"

    def __str__(self):
        # # Фолбэк на профильные ФИО, затем на user.username
        first_name = (self.first_name or self.user.first_name or self.user.username)
        last_name = (self.last_name or self.user.last_name or "")
        return f"{first_name} {last_name}".strip()
    
    def get_groups_count(self):
        """Получить количество групп тренера"""
        return self.traininggroup_set.count()
    
    def get_athletes_count(self):
        """Получить количество спортсменов тренера"""
        total = 0
        for group in self.traininggroup_set.all():
            total += group.athletetraininggroup_set.count()
        return total

class Staff(models.Model):
    """Сотрудник (вспомогательные роли)"""
    ROLE_CHOICES = [
        ('manager', 'Менеджер'),  # оставляем только менеджера
    ]
    
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='manager', verbose_name="Роль")
    subrole = models.CharField(max_length=100, null=True, blank=True, verbose_name="Подроль")  # оставляем поле для совместимости, но не используем
    is_archived = models.BooleanField(default=False, verbose_name="Архивирован")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивирования")
    archived_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Архивирован кем")
    phone = models.CharField(max_length=255, unique=True, verbose_name="Телефон")
    birth_date = models.DateField(verbose_name="Дата рождения")
    # Новые поля ФИО на профиль сотрудника
    first_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="Фамилия")

    class Meta:
        db_table = 'staff'
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def get_role_display(self):
        """Получить отображаемое название роли"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    def __str__(self):
        first_name = (self.first_name or self.user.first_name or self.user.username)
        last_name = (self.last_name or self.user.last_name or "")
        return f"{last_name} {first_name} ({self.get_role_display()})".strip()

class Parent(models.Model):
    """Родитель"""
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    phone = models.CharField(max_length=255, null=True, blank=True, unique=True, default=None, verbose_name="Телефон")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    is_archived = models.BooleanField(default=False, verbose_name="Архивирован")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивирования")
    archived_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Архивирован кем")

    class Meta:
        db_table = 'parent'
        verbose_name = "Родитель"
        verbose_name_plural = "Родители"

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}".strip()
    
    def get_children_relations(self):
        """Связи Parent↔Athlete (AthleteParent) с предзагрузкой пользователя ребёнка"""
        return self.athleteparent_set.select_related('athlete__user')

    def get_children(self):
        """Получить queryset объектов Athlete, связанных с данным родителем"""
        from .models import Athlete  # локально, чтобы избежать циклического импорта при миграциях
        return (
            Athlete.objects
            .filter(athleteparent__parent=self)
            .select_related('user')
            .distinct()
        )

class Athlete(models.Model):
    """Спортсмен"""
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    birth_date = models.DateField(verbose_name="Дата рождения")
    phone = models.CharField(max_length=255, null=True, blank=True, unique=True, default=None, verbose_name="Телефон")
    is_archived = models.BooleanField(default=False, verbose_name="Архивирован")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивирования")
    archived_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Архивирован кем")
    # Новые поля ФИО на профиль спортсмена
    first_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=150, null=True, blank=True, verbose_name="Фамилия")

    class Meta:
        db_table = 'athlete'
        verbose_name = "Спортсмен"
        verbose_name_plural = "Спортсмены"

    def __str__(self):
        first_name = (self.first_name or self.user.first_name or self.user.username)
        last_name = (self.last_name or self.user.last_name or "")
        return f"{last_name} {first_name}".strip()
    
    def get_parents(self):
        """Получить связанных родителей"""
        return self.athleteparent_set.all()
    
    def get_parents_display(self):
        """Получить отображение родителей для админки"""
        parents = self.get_parents()
        if parents:
            return ", ".join([f"{parent.parent.user.first_name} {parent.parent.user.last_name}" for parent in parents])
        return "Не указаны"

class TrainingGroup(models.Model):
    """Тренировочная группа"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, verbose_name="Название")
    age_min = models.IntegerField(verbose_name="Минимальный возраст")
    age_max = models.IntegerField(default=18, verbose_name="Максимальный возраст")
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Тренер")
    max_athletes = models.IntegerField(default=20, verbose_name="Максимум спортсменов")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    is_archived = models.BooleanField(default=False, verbose_name="Архивирована")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивирования")
    archived_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='traininggroup_archived_by_set', verbose_name="Архивирована кем")

    class Meta:
        db_table = 'training_group'
        verbose_name = "Тренировочная группа"
        verbose_name_plural = "Тренировочные группы"

    def __str__(self):
        trainer_name = f" - {self.trainer}" if self.trainer else ""
        return f"{self.name}{trainer_name}"
    
    def get_athletes_count(self):
        """Получить количество спортсменов в группе"""
        return self.athletetraininggroup_set.count()
    
    def get_parents_count(self):
        """Получить количество родителей в группе"""
        parents = set()
        for athlete_group in self.athletetraininggroup_set.all():
            for athlete_parent in athlete_group.athlete.athleteparent_set.all():
                parents.add(athlete_parent.parent)
        return len(parents)

class AthleteTrainingGroup(models.Model):
    """Связь спортсмен-тренировочная группа"""
    id = models.BigAutoField(primary_key=True)
    athlete = models.ForeignKey(Athlete, on_delete=models.CASCADE, verbose_name="Спортсмен")
    training_group = models.ForeignKey(TrainingGroup, on_delete=models.CASCADE, verbose_name="Тренировочная группа")

    class Meta:
        db_table = 'athlete_training_group'
        verbose_name = "Спортсмен в группе"
        verbose_name_plural = "Спортсмены в группах"
        unique_together = ('athlete', 'training_group')

    def __str__(self):
        return f"{self.athlete} - {self.training_group}"

class AthleteParent(models.Model):
    """Связь спортсмен-родитель"""
    id = models.BigAutoField(primary_key=True)
    athlete = models.ForeignKey(Athlete, on_delete=models.CASCADE, verbose_name="Спортсмен")
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, verbose_name="Родитель")

    class Meta:
        db_table = 'athlete_parent'
        verbose_name = "Связь спортсмен-родитель"
        verbose_name_plural = "Связи спортсмен-родитель"
        unique_together = ('athlete', 'parent')

    def __str__(self):
        return f"{self.athlete} - {self.parent}"

class GroupSchedule(models.Model):
    """Расписание группы"""
    id = models.AutoField(primary_key=True)
    training_group = models.ForeignKey(TrainingGroup, on_delete=models.CASCADE, verbose_name="Тренировочная группа")
    weekday = models.IntegerField(verbose_name="День недели")  # 1-7 (Пн-Вс)
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")

    class Meta:
        db_table = 'group_schedule'
        verbose_name = "Расписание группы"
        verbose_name_plural = "Расписания групп"
        unique_together = ('training_group', 'weekday', 'start_time')

    def __str__(self):
        return f"{self.training_group} - День {self.weekday}"

class TrainingSession(models.Model):
    """Тренировочная сессия"""
    id = models.AutoField(primary_key=True)
    training_group = models.ForeignKey(TrainingGroup, on_delete=models.CASCADE, verbose_name="Тренировочная группа")
    date = models.DateField(verbose_name="Дата")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    is_closed = models.BooleanField(default=False, verbose_name="Закрыта")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_canceled = models.BooleanField(default=False, verbose_name="Отменена")
    canceled_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Отменена кем")
    canceled_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата отмены")

    class Meta:
        db_table = 'training_session'
        verbose_name = "Тренировочная сессия"
        verbose_name_plural = "Тренировочные сессии"

    def __str__(self):
        return f"{self.training_group} - {self.date}"

class AttendanceRecord(models.Model):
    """Запись посещаемости"""
    id = models.AutoField(primary_key=True)
    athlete = models.ForeignKey(Athlete, on_delete=models.CASCADE, verbose_name="Спортсмен")
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, verbose_name="Сессия")
    was_present = models.BooleanField(verbose_name="Присутствовал")
    marked_at = models.DateTimeField(auto_now_add=True, verbose_name="Время отметки")
    marked_by = models.ForeignKey(Staff, on_delete=models.CASCADE, verbose_name="Отметил")

    class Meta:
        db_table = 'attendance_record'
        verbose_name = "Запись посещаемости"
        verbose_name_plural = "Записи посещаемости"
        unique_together = ('athlete', 'session')

    def __str__(self):
        return f"{self.athlete} - {self.session}"

class DocumentType(models.Model):
    """Тип документа"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, verbose_name="Название")

    class Meta:
        db_table = 'document_type'
        verbose_name = "Тип документа"
        verbose_name_plural = "Типы документов"

    def __str__(self):
        return self.name

class Document(models.Model):
    """Документ"""
    id = models.AutoField(primary_key=True)
    file = models.CharField(max_length=255, verbose_name="Файл")  # Путь к файлу
    file_type = models.CharField(max_length=255, verbose_name="Тип файла")
    file_size = models.IntegerField(verbose_name="Размер файла")
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, verbose_name="Тип документа")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name="Тип контента")
    object_id = models.BigIntegerField(verbose_name="ID объекта")
    content_object = GenericForeignKey('content_type', 'object_id')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Загружен кем")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    is_private = models.BooleanField(default=False, verbose_name="Приватный")
    comment = models.TextField(default="", verbose_name="Комментарий")
    is_archived = models.BooleanField(default=False, verbose_name="Архивирован")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивирования")
    archived_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Архивирован кем")

    class Meta:
        db_table = 'document'
        verbose_name = "Документ"
        verbose_name_plural = "Документы"

    def __str__(self):
        return f"{self.document_type.name} - {self.comment}"

class Payment(models.Model):
    """Платеж"""
    id = models.AutoField(primary_key=True)
    athlete = models.ForeignKey(Athlete, on_delete=models.CASCADE, verbose_name="Спортсмен")
    training_group = models.ForeignKey(TrainingGroup, on_delete=models.CASCADE, verbose_name="Тренировочная группа")
    payer = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Плательщик")
    amount = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Сумма")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, verbose_name="Способ оплаты")
    comment = models.TextField(default="", verbose_name="Комментарий")
    billing_period_start = models.DateField(verbose_name="Начало периода оплаты")
    billing_period_end = models.DateField(verbose_name="Конец периода оплаты")
    is_archived = models.BooleanField(default=False, verbose_name="Архивирован")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата оплаты")
    is_automated = models.BooleanField(verbose_name="Автоматизирован")
    is_paid = models.BooleanField(default=False, verbose_name="Оплачен")
    invoice_number = models.CharField(max_length=255, unique=True, verbose_name="Номер счета")
    created_by = models.ForeignKey(Staff, on_delete=models.CASCADE, verbose_name="Создан кем")
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата архивирования")
    archived_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_archived_by_set', verbose_name="Архивирован кем")

    class Meta:
        db_table = 'payment'
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return self.invoice_number  # Возвращаем номер счета

class AuditRecord(models.Model):
    """Запись аудита"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    action = models.CharField(max_length=255, verbose_name="Действие")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name="Тип контента")
    object_id = models.BigIntegerField(verbose_name="ID объекта")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Временная метка")
    details = models.TextField(default="", verbose_name="Детали")

    class Meta:
        db_table = 'audit_record'
        verbose_name = "Запись аудита"
        verbose_name_plural = "Записи аудита"

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"


class RegistrationDraft(models.Model):
    """Черновик регистрации пользователя в 4 шага.

    Создается на шаге 1 вместе с временным пользователем (user.is_active=False).
    Хранит выбранную роль и текущий шаг. Для сотрудника хранит подроль.
    При удалении незавершенного черновика автоматически удаляет временного пользователя.
    """

    ROLE_CHOICES = (
        ("trainer", "Тренер"),
        ("parent", "Родитель"),
        ("athlete", "Спортсмен"),
        ("staff", "Сотрудник"),  # добавили тип сотрудник
    )

    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="registration_draft",
                                verbose_name="Временный пользователь")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_registration_drafts",
                                   verbose_name="Кем начато")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True, verbose_name="Роль")
    staff_role = models.CharField(max_length=100, null=True, blank=True, verbose_name="Подроль сотрудника")  # для staff
    current_step = models.PositiveSmallIntegerField(default=1, verbose_name="Текущий шаг")
    is_completed = models.BooleanField(default=False, verbose_name="Завершено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        db_table = "registration_draft"
        verbose_name = "Черновик регистрации"
        verbose_name_plural = "Черновики регистрации"

    def __str__(self) -> str:
        return f"Draft #{self.pk} by {self.created_by} for {self.user} (step {self.current_step})"

    def safe_dispose(self):
        """Безопасно удалить черновик и связанного временного пользователя.
        Используется при отмене/уходе со страницы и при входе на /register/.
        """
        temp_user = self.user
        try:
            super().delete()  # удалит запись черновика
        finally:
            # Удаляем временного пользователя, если он еще существует
            try:
                if temp_user and not temp_user.is_active:
                    temp_user.delete()
            except User.DoesNotExist:
                pass


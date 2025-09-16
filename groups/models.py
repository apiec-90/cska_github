from django.db import models
from django.core.validators import MinValueValidator

class Group(models.Model):
    """Модель спортивной группы"""
    
    AGE_CHOICES = [
        (6, '6 лет'),
        (7, '7 лет'),
        (8, '8 лет'),
        (9, '9 лет'),
        (10, '10 лет'),
        (11, '11 лет'),
        (12, '12 лет'),
        (13, '13 лет'),
        (14, '14 лет'),
        (15, '15 лет'),
        (16, '16 лет'),
        (17, '17 лет'),
        (18, '18+ лет'),
    ]
    
    DAYS_CHOICES = [
        ('mon', 'Понедельник'),
        ('tue', 'Вторник'),
        ('wed', 'Среда'),
        ('thu', 'Четверг'),
        ('fri', 'Пятница'),
        ('sat', 'Суббота'),
        ('sun', 'Воскресенье'),
    ]
    
    number = models.IntegerField(
        verbose_name="Номер группы",
        unique=True,
        validators=[MinValueValidator(1)]
    )
    
    age_min = models.IntegerField(
        verbose_name="Минимальный возраст",
        choices=AGE_CHOICES,
        default=6
    )
    
    age_max = models.IntegerField(
        verbose_name="Максимальный возраст", 
        choices=AGE_CHOICES,
        default=18
    )
    
    trainer = models.CharField(
        verbose_name="Тренер",
        max_length=100
    )
    
    days = models.JSONField(
        verbose_name="Дни недели",
        default=list,
        help_text="Список дней недели для занятий"
    )
    
    time = models.TimeField(
        verbose_name="Время занятий"
    )
    
    is_active = models.BooleanField(
        verbose_name="Активная группа",
        default=True
    )
    
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True
    )
    
    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ['number']
    
    def __str__(self):
        return f"Группа {self.number} ({self.age_min}-{self.age_max} лет)"
    
    @property
    def athletes_count(self):
        """Количество спортсменов в группе"""
        return self.athletes.filter(is_active=True).count()
    
    @property
    def age_display(self):
        """Отображение возраста в формате 8-9 лет или 18+"""
        if self.age_max == 18:
            return f"{self.age_min}+"
        return f"{self.age_min}-{self.age_max}"
    
    @property
    def days_display(self):
        """Отображение дней недели в читаемом формате"""
        day_names = dict(self.DAYS_CHOICES)
        return ", ".join([day_names[day] for day in self.days])

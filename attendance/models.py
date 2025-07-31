from django.db import models
from athletes.models import Athlete
from datetime import date

class Attendance(models.Model):
    """Модель посещаемости спортсменов"""
    
    PRESENCE_CHOICES = [
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('late', 'Опоздал'),
    ]
    
    athlete = models.ForeignKey(
        Athlete,
        verbose_name="Спортсмен",
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    
    date = models.DateField(
        verbose_name="Дата",
        default=date.today
    )
    
    status = models.CharField(
        verbose_name="Статус посещения",
        max_length=10,
        choices=PRESENCE_CHOICES,
        default='present'
    )
    
    notes = models.TextField(
        verbose_name="Заметки",
        blank=True,
        help_text="Дополнительные заметки о посещении"
    )
    
    created_at = models.DateTimeField(
        verbose_name="Дата создания записи",
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True
    )
    
    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"
        ordering = ['-date', 'athlete__last_name']
        unique_together = ['athlete', 'date']  # Одна запись на спортсмена в день
    
    def __str__(self):
        return f"{self.athlete.full_name} - {self.date} ({self.get_status_display()})"
    
    @property
    def is_present(self):
        """Был ли спортсмен на занятии"""
        return self.status == 'present'
    
    @property
    def status_icon(self):
        """Иконка статуса посещения"""
        icons = {
            'present': '✅',
            'absent': '❌',
            'late': '⏰'
        }
        return icons.get(self.status, '❓')
    
    @property
    def status_color(self):
        """Цвет статуса для отображения"""
        colors = {
            'present': 'text-green-600',
            'absent': 'text-red-600', 
            'late': 'text-yellow-600'
        }
        return colors.get(self.status, 'text-gray-600')

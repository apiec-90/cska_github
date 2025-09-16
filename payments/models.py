from django.db import models
from athletes.models import Athlete
 

class Payment(models.Model):
    """Модель оплаты спортсменов"""
    
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Оплачено'),
        ('unpaid', 'Не оплачено'),
        ('partial', 'Частично оплачено'),
    ]
    
    athlete = models.ForeignKey(
        Athlete,
        verbose_name="Спортсмен",
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    month = models.DateField(
        verbose_name="Месяц оплаты",
        help_text="Первый день месяца"
    )
    
    amount = models.DecimalField(
        verbose_name="Сумма к оплате",
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    paid_amount = models.DecimalField(
        verbose_name="Оплаченная сумма",
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    status = models.CharField(
        verbose_name="Статус оплаты",
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid'
    )
    
    payment_date = models.DateField(
        verbose_name="Дата оплаты",
        blank=True,
        null=True
    )
    
    notes = models.TextField(
        verbose_name="Заметки",
        blank=True,
        help_text="Дополнительные заметки об оплате"
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
        verbose_name = "Оплата"
        verbose_name_plural = "Оплаты"
        ordering = ['-month', 'athlete__last_name']
        unique_together = ['athlete', 'month']  # Одна запись на спортсмена в месяц
    
    def __str__(self):
        return f"{self.athlete.full_name} - {self.month.strftime('%B %Y')} ({self.get_status_display()})"
    
    @property
    def month_display(self):
        """Отображение месяца в формате 'Январь 2024'"""
        return self.month.strftime('%B %Y')
    
    @property
    def month_short(self):
        """Короткое отображение месяца 'Янв 2024'"""
        return self.month.strftime('%b %Y')
    
    @property
    def is_paid(self):
        """Полностью ли оплачено"""
        return self.status == 'paid'
    
    @property
    def is_unpaid(self):
        """Не оплачено ли"""
        return self.status == 'unpaid'
    
    @property
    def is_partial(self):
        """Частично ли оплачено"""
        return self.status == 'partial'
    
    @property
    def remaining_amount(self):
        """Оставшаяся сумма к оплате"""
        return self.amount - self.paid_amount
    
    @property
    def status_icon(self):
        """Иконка статуса оплаты"""
        icons = {
            'paid': '✅',
            'unpaid': '❌',
            'partial': '⚠️'
        }
        return icons.get(self.status, '❓')
    
    @property
    def status_color(self):
        """Цвет статуса для отображения"""
        colors = {
            'paid': 'text-green-600',
            'unpaid': 'text-red-600',
            'partial': 'text-yellow-600'
        }
        return colors.get(self.status, 'text-gray-600')
    
    @property
    def row_color(self):
        """Цвет строки для отображения"""
        colors = {
            'paid': 'bg-green-50',
            'unpaid': 'bg-red-50', 
            'partial': 'bg-yellow-50'
        }
        return colors.get(self.status, 'bg-white')
    
    def save(self, *args, **kwargs):
        """Автоматически обновляем статус при изменении сумм"""
        if self.paid_amount >= self.amount and self.amount > 0:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        else:
            self.status = 'unpaid'
        
        # Устанавливаем дату оплаты если оплачено
        if self.status == 'paid' and not self.payment_date:
            from datetime import date
            self.payment_date = date.today()
        
        super().save(*args, **kwargs)

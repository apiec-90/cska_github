from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Админка для оплаты"""
    
    list_display = [
        'athlete',
        'month_short',
        'amount',
        'paid_amount',
        'remaining_amount',
        'status_icon',
        'status'
    ]
    
    list_filter = [
        'status',
        'month',
        'athlete__group'
    ]
    
    search_fields = [
        'athlete__first_name',
        'athlete__last_name'
    ]
    
    list_editable = ['amount', 'paid_amount', 'status']
    
    ordering = ['-month', 'athlete__last_name']
    
    date_hierarchy = 'month'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('athlete', 'month', 'status')
        }),
        ('Финансовая информация', {
            'fields': ('amount', 'paid_amount', 'payment_date')
        }),
        ('Дополнительно', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at', 'remaining_amount']
    
    def get_queryset(self, request):
        """Оптимизация: предзагружаем спортсмена для списков."""
        qs = super().get_queryset(request)
        return qs.select_related('athlete')
    
    def month_short(self, obj):
        """Короткое отображение месяца"""
        return obj.month_short
    month_short.short_description = "Месяц"
    
    def remaining_amount(self, obj):
        """Оставшаяся сумма"""
        return obj.remaining_amount
    remaining_amount.short_description = "Остаток"
    
    def status_icon(self, obj):
        """Иконка статуса оплаты"""
        return obj.status_icon
    status_icon.short_description = ""

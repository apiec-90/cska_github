from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Админка для посещаемости"""
    
    list_display = [
        'athlete',
        'date',
        'status_icon',
        'status',
        'notes_short'
    ]
    
    list_filter = [
        'status',
        'date',
        'athlete__group'
    ]
    
    search_fields = [
        'athlete__first_name',
        'athlete__last_name',
        'notes'
    ]
    
    list_editable = ['status']
    
    ordering = ['-date', 'athlete__last_name']
    
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('athlete', 'date', 'status')
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
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Оптимизация: предзагружаем спортсмена для списков."""
        qs = super().get_queryset(request)
        return qs.select_related('athlete')
    
    def status_icon(self, obj):
        """Иконка статуса посещения"""
        return obj.status_icon
    status_icon.short_description = ""
    
    def notes_short(self, obj):
        """Короткая версия заметок"""
        if obj.notes:
            return obj.notes[:50] + "..." if len(obj.notes) > 50 else obj.notes
        return "-"
    notes_short.short_description = "Заметки"

from django.contrib import admin
from .models import Group

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Админка для групп"""
    
    list_display = [
        'number', 
        'age_display', 
        'trainer', 
        'days_display', 
        'time', 
        'athletes_count',
        'is_active'
    ]
    
    list_filter = [
        'is_active',
        'age_min',
        'age_max', 
        'trainer'
    ]
    
    search_fields = [
        'number',
        'trainer'
    ]
    
    list_editable = ['is_active']
    
    ordering = ['number']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'trainer', 'is_active')
        }),
        ('Возрастная группа', {
            'fields': ('age_min', 'age_max')
        }),
        ('Расписание', {
            'fields': ('days', 'time')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at', 'athletes_count']
    
    def athletes_count(self, obj):
        """Количество спортсменов в группе"""
        return obj.athletes_count
    athletes_count.short_description = "Спортсменов"
    
    def age_display(self, obj):
        """Отображение возраста"""
        return obj.age_display
    age_display.short_description = "Возраст"
    
    def days_display(self, obj):
        """Отображение дней недели"""
        return obj.days_display
    days_display.short_description = "Дни недели"

from django.contrib import admin
from .models import Athlete, Document

class DocumentInline(admin.TabularInline):
    """Встроенное отображение документов в админке спортсмена"""
    model = Document
    extra = 0
    fields = ['title', 'file', 'file_type', 'uploaded_at']
    readonly_fields = ['file_type', 'uploaded_at']

@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    """Админка для спортсменов"""
    
    list_display = [
        'full_name',
        'group',
        'age',
        'birth_date_display',
        'phone',
        'is_active'
    ]
    
    list_filter = [
        'is_active',
        'group',
        'birth_date'
    ]
    
    search_fields = [
        'first_name',
        'last_name',
        'phone'
    ]
    
    list_editable = ['is_active']
    
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'group', 'is_active')
        }),
        ('Контактная информация', {
            'fields': ('birth_date', 'phone')
        }),
        ('Фото', {
            'fields': ('photo',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at', 'age']
    
    inlines = [DocumentInline]
    
    def full_name(self, obj):
        """Полное имя спортсмена"""
        return obj.full_name
    full_name.short_description = "ФИО"
    
    def age(self, obj):
        """Возраст спортсмена"""
        return f"{obj.age} лет"
    age.short_description = "Возраст"
    
    def birth_date_display(self, obj):
        """Дата рождения в формате дд.мм.гггг"""
        return obj.birth_date_display
    birth_date_display.short_description = "Дата рождения"

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Админка для документов"""
    
    list_display = [
        'title',
        'athlete',
        'file_type',
        'file_icon',
        'file_size_display',
        'uploaded_at'
    ]
    
    list_filter = [
        'file_type',
        'uploaded_at',
        'athlete__group'
    ]
    
    search_fields = [
        'title',
        'athlete__first_name',
        'athlete__last_name'
    ]
    
    ordering = ['-uploaded_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('athlete', 'title', 'file')
        }),
        ('Системная информация', {
            'fields': ('file_type', 'uploaded_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['file_type', 'uploaded_at', 'file_icon', 'file_size_display']
    
    def file_icon(self, obj):
        """Иконка типа файла"""
        return obj.file_icon
    file_icon.short_description = "Тип"
    
    def file_size_display(self, obj):
        """Размер файла"""
        return obj.file_size_display
    file_size_display.short_description = "Размер"

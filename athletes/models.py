from django.db import models
from django.core.validators import RegexValidator
from groups.models import Group
import os

def athlete_photo_path(instance, filename):
    """Путь для сохранения фото спортсмена"""
    return f'athletes/{instance.id}/photo/{filename}'

def athlete_document_path(instance, filename):
    """Путь для сохранения документов спортсмена"""
    return f'athletes/{instance.athlete.id}/documents/{filename}'

class Athlete(models.Model):
    """Модель спортсмена"""
    
    # Валидатор для телефона в формате +7-xxx-xxx-xx-xx
    phone_regex = RegexValidator(
        regex=r'^\+7-\d{3}-\d{3}-\d{2}-\d{2}$',
        message='Телефон должен быть в формате: +7-xxx-xxx-xx-xx'
    )
    
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=50
    )
    
    last_name = models.CharField(
        verbose_name="Фамилия", 
        max_length=50
    )
    
    group = models.ForeignKey(
        Group,
        verbose_name="Группа",
        on_delete=models.CASCADE,
        related_name='athletes'
    )
    
    birth_date = models.DateField(
        verbose_name="Дата рождения"
    )
    
    phone = models.CharField(
        verbose_name="Телефон",
        max_length=18,
        validators=[phone_regex],
        help_text="Формат: +7-xxx-xxx-xx-xx"
    )
    
    photo = models.ImageField(
        verbose_name="Фото",
        upload_to=athlete_photo_path,
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(
        verbose_name="Активный спортсмен",
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
        verbose_name = "Спортсмен"
        verbose_name_plural = "Спортсмены"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    
    @property
    def full_name(self):
        """Полное имя спортсмена"""
        return f"{self.last_name} {self.first_name}"
    
    @property
    def age(self):
        """Возраст спортсмена"""
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @property
    def birth_date_display(self):
        """Дата рождения в формате дд.мм.гггг"""
        return self.birth_date.strftime('%d.%m.%Y')

class Document(models.Model):
    """Модель документа спортсмена"""
    
    DOCUMENT_TYPES = [
        ('pdf', 'PDF документ'),
        ('doc', 'Word документ'),
        ('docx', 'Word документ'),
        ('jpg', 'Изображение JPG'),
        ('jpeg', 'Изображение JPEG'),
        ('png', 'Изображение PNG'),
        ('other', 'Другой файл'),
    ]
    
    athlete = models.ForeignKey(
        Athlete,
        verbose_name="Спортсмен",
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    title = models.CharField(
        verbose_name="Название документа",
        max_length=200
    )
    
    file = models.FileField(
        verbose_name="Файл",
        upload_to=athlete_document_path
    )
    
    file_type = models.CharField(
        verbose_name="Тип файла",
        max_length=10,
        choices=DOCUMENT_TYPES,
        default='other'
    )
    
    uploaded_at = models.DateTimeField(
        verbose_name="Дата загрузки",
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.athlete.full_name}"
    
    def save(self, *args, **kwargs):
        """Автоматически определяем тип файла при сохранении"""
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext == '.pdf':
                self.file_type = 'pdf'
            elif ext in ['.doc', '.docx']:
                self.file_type = ext[1:]  # убираем точку
            elif ext in ['.jpg', '.jpeg']:
                self.file_type = ext[1:]
            elif ext == '.png':
                self.file_type = 'png'
            else:
                self.file_type = 'other'
        super().save(*args, **kwargs)
    
    @property
    def file_icon(self):
        """Иконка для типа файла"""
        icons = {
            'pdf': '📄',
            'doc': '📝',
            'docx': '📝', 
            'jpg': '🖼️',
            'jpeg': '🖼️',
            'png': '🖼️',
            'other': '📎'
        }
        return icons.get(self.file_type, '📎')
    
    @property
    def file_size_display(self):
        """Размер файла в читаемом формате"""
        if self.file:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return "0 B"

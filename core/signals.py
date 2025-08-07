from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from .models import Staff, Parent, Athlete, TrainingGroup, Document, AuditRecord

@receiver(post_save, sender=Staff)
def sync_staff_archive(sender, instance, **kwargs):
    """Синхронизация архивирования Staff с User"""
    if instance.user:
        if instance.is_archived and instance.user.is_active:
            # Деактивируем User при архивировании Staff
            instance.user.is_active = False
            instance.user.save(update_fields=['is_active'])
        elif not instance.is_archived and not instance.user.is_active:
            # Активируем User при восстановлении Staff
            instance.user.is_active = True
            instance.user.save(update_fields=['is_active'])

@receiver(post_save, sender=Parent)
def sync_parent_archive(sender, instance, **kwargs):
    """Синхронизация архивирования Parent с User"""
    if instance.user:
        if instance.is_archived and instance.user.is_active:
            # Деактивируем User при архивировании Parent
            instance.user.is_active = False
            instance.user.save(update_fields=['is_active'])
        elif not instance.is_archived and not instance.user.is_active:
            # Активируем User при восстановлении Parent
            instance.user.is_active = True
            instance.user.save(update_fields=['is_active'])

@receiver(post_save, sender=Athlete)
def sync_athlete_archive(sender, instance, **kwargs):
    """Синхронизация архивирования Athlete с User"""
    if instance.user:
        if instance.is_archived and instance.user.is_active:
            # Деактивируем User при архивировании Athlete
            instance.user.is_active = False
            instance.user.save(update_fields=['is_active'])
        elif not instance.is_archived and not instance.user.is_active:
            # Активируем User при восстановлении Athlete
            instance.user.is_active = True
            instance.user.save(update_fields=['is_active'])

@receiver(post_save, sender=Document)
def log_document_upload(sender, instance, created, **kwargs):
    """Логирование загрузки документа"""
    if created:
        # Создаем запись аудита
        AuditRecord.objects.create(
            user=instance.uploaded_by,
            action='upload_document',
            content_type=ContentType.objects.get_for_model(Document),
            object_id=instance.id,
            details=f"Загружен документ: {instance.document_type.name} - {instance.comment}"
        )

@receiver(pre_save, sender=Staff)
def log_staff_changes(sender, instance, **kwargs):
    """Логирование изменений Staff"""
    if instance.pk:  # Только для существующих записей
        try:
            old_instance = Staff.objects.get(pk=instance.pk)
            if (old_instance.phone != instance.phone or
                old_instance.birth_date != instance.birth_date or
                old_instance.is_archived != instance.is_archived):
                
                AuditRecord.objects.create(
                    user=instance.user,
                    action='update_staff',
                    content_type=ContentType.objects.get_for_model(Staff),
                    object_id=instance.id,
                    details=f"Изменены данные сотрудника: {instance.user.first_name} {instance.user.last_name}"
                )
        except Staff.DoesNotExist:
            pass

@receiver(pre_save, sender=Athlete)
def log_athlete_changes(sender, instance, **kwargs):
    """Логирование изменений Athlete"""
    if instance.pk:  # Только для существующих записей
        try:
            old_instance = Athlete.objects.get(pk=instance.pk)
            if (old_instance.birth_date != instance.birth_date or
                old_instance.is_archived != instance.is_archived):
                
                AuditRecord.objects.create(
                    user=instance.user,
                    action='update_athlete',
                    content_type=ContentType.objects.get_for_model(Athlete),
                    object_id=instance.id,
                    details=f"Изменены данные спортсмена: {instance.user.first_name} {instance.user.last_name}"
                )
        except Athlete.DoesNotExist:
            pass

@receiver(pre_save, sender=TrainingGroup)
def log_training_group_changes(sender, instance, **kwargs):
    """Логирование изменений TrainingGroup"""
    if instance.pk:  # Только для существующих записей
        try:
            old_instance = TrainingGroup.objects.get(pk=instance.pk)
            if (old_instance.name != instance.name or
                old_instance.age_min != instance.age_min or
                old_instance.age_max != instance.age_max or
                old_instance.is_archived != instance.is_archived):
                
                AuditRecord.objects.create(
                    user=instance.staff.user if instance.staff else None,
                    action='update_training_group',
                    content_type=ContentType.objects.get_for_model(TrainingGroup),
                    object_id=instance.id,
                    details=f"Изменены данные группы: {instance.name}"
                )
        except TrainingGroup.DoesNotExist:
            pass 
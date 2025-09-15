from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from .models import Staff, Parent, Athlete, Trainer, TrainingGroup, Document, AuditRecord, GroupSchedule
from .utils.sessions import resync_future_sessions_for_group
import os

# Упрощенный маппинг - основные роли
GROUP_MODEL_MAPPING = {
    'Родители': {
        'model': Parent,
        'role': None,  # Прямые допуски к группе
    },
    'Спортсмены': {
        'model': Athlete,
        'role': None,  # Прямые допуски к группе
    },
    'Тренеры': {
        'model': Trainer,
        'role': None,  # Тренеры без ролей
    },
    'Менеджеры': {
        'model': Staff,
        'role': 'manager',  # Менеджеры
    },
}

# ВРЕМЕННО ОТКЛЮЧЕНО - создание записей ролей перенесено в админские представления
# @receiver(m2m_changed, sender=User.groups.through)
# def create_role_records(sender, instance, action, pk_set, **kwargs):
#     """Создает записи в соответствующих моделях при добавлении пользователя в группу"""
#     # Сигнал отключен - записи создаются в админских представлениях после заполнения профиля
#     pass

@receiver(m2m_changed, sender=User.groups.through)
def remove_role_records(sender, instance, action, pk_set, **kwargs):
    """Удаляет записи при удалении пользователя из группы (опционально)"""
    if os.environ.get('DISABLE_SIGNALS'):
        return
        
    if action == "post_remove":  # При удалении из группы
        user = instance
        
        # Получаем удаленные группы
        removed_groups = Group.objects.filter(pk__in=pk_set)
        
        for group in removed_groups:
            if group.name in GROUP_MODEL_MAPPING:
                # Обработка специальных групп
                config = GROUP_MODEL_MAPPING[group.name]
                model_class = config['model']

                # Никогда не удаляем текущую запись Staff при изменении групп
                if model_class is Staff:
                    AuditRecord.objects.create(
                        user=user,
                        action='remove_from_group',
                        content_type=ContentType.objects.get_for_model(Group),
                        object_id=group.id,
                        details=f"Пользователь удален из группы {group.name}, запись Staff оставлена"
                    )
                else:
                    # Находим и удаляем профильную запись для других моделей
                    existing_record = model_class.objects.filter(user=user).first()
                    if existing_record:
                        # Сохраняем ID перед удалением для логирования
                        record_id = existing_record.id
                        existing_record.delete()
                        print(f"Удалена запись {model_class.__name__} для пользователя {user.username} из группы {group.name}")

                        # Логируем удаление
                        AuditRecord.objects.create(
                            user=user,
                            action=f'delete_{model_class.__name__.lower()}',
                            content_type=ContentType.objects.get_for_model(model_class),
                            object_id=record_id,
                            details=f"Автоматически удалена запись {model_class.__name__} при удалении из группы {group.name}"
                        )
            else:
                # Для новых групп - НЕ удаляем Staff, только логируем
                existing_staff = Staff.objects.filter(user=user).first()
                if existing_staff:
                    print(f"Пользователь {user.username} удален из группы {group.name}, но запись Staff сохранена")
                    
                    # Логируем удаление из группы
                    AuditRecord.objects.create(
                        user=user,
                        action='remove_from_group',
                        content_type=ContentType.objects.get_for_model(Group),
                        object_id=group.id,
                        details=f"Пользователь удален из группы {group.name}, запись Staff сохранена"
                    )

@receiver(post_save, sender=Staff)
def sync_staff_role_to_group(sender, instance, **kwargs):
    """Синхронизация роли Staff с группой Django"""
    if os.environ.get('DISABLE_SIGNALS'):
        return
    if instance.role == 'manager':
        # Убираем из всех ролевых групп
        role_groups = Group.objects.filter(name__in=['Менеджеры'])
        for group in role_groups:
            instance.user.groups.remove(group)
        
        # Добавляем в нужную группу на основе роли
        if instance.role == 'manager':
            group = Group.objects.get_or_create(name='Менеджеры')[0]
            # Убираем ссылку на несуществующее поле staff_role
            instance.user.groups.add(group)

@receiver(post_save, sender=Staff)
def sync_staff_archive(sender, instance, **kwargs):
    """Синхронизация архивирования Staff с User"""
    if os.environ.get('DISABLE_SIGNALS'):
        return
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

@receiver(post_save, sender=Trainer)
def sync_trainer_archive(sender, instance, **kwargs):
    """Синхронизация архивирования Trainer с User"""
    if instance.user:
        if instance.is_archived and instance.user.is_active:
            # Деактивируем User при архивировании Trainer
            instance.user.is_active = False
            instance.user.save(update_fields=['is_active'])
        elif not instance.is_archived and not instance.user.is_active:
            # Активируем User при восстановлении Trainer
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

@receiver(pre_save, sender=Trainer)
def log_trainer_changes(sender, instance, **kwargs):
    """Логирование изменений Trainer"""
    if instance.pk:  # Только для существующих записей
        try:
            old_instance = Trainer.objects.get(pk=instance.pk)
            if (old_instance.phone != instance.phone or
                old_instance.birth_date != instance.birth_date or
                old_instance.is_archived != instance.is_archived):
                
                AuditRecord.objects.create(
                    user=instance.user,
                    action='update_trainer',
                    content_type=ContentType.objects.get_for_model(Trainer),
                    object_id=instance.id,
                    details=f"Изменены данные тренера: {instance.user.first_name} {instance.user.last_name}"
                )
        except Trainer.DoesNotExist:
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
                    user=instance.trainer.user if instance.trainer else None,
                    action='update_training_group',
                    content_type=ContentType.objects.get_for_model(TrainingGroup),
                    object_id=instance.id,
                    details=f"Изменены данные группы: {instance.name}"
                )
        except TrainingGroup.DoesNotExist:
            pass

@receiver([post_save, post_delete], sender=GroupSchedule)
def on_schedule_change(sender, instance, **kwargs):
    """Автосинхронизация сессий при изменении расписания группы"""
    resync_future_sessions_for_group(instance.training_group)
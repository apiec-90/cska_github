from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from .models import Staff, Parent, Athlete, Trainer, TrainingGroup, Document, AuditRecord

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

@receiver(m2m_changed, sender=User.groups.through)
def create_role_records(sender, instance, action, pk_set, **kwargs):
    """Создает записи в соответствующих моделях при добавлении пользователя в группу"""
    if action == "post_add":  # Только при добавлении в группу
        user = instance
        
        # Получаем все группы пользователя
        user_groups = user.groups.all()
        
        for group in user_groups:
            if group.name in GROUP_MODEL_MAPPING:
                # Обработка специальных групп (Родители, Спортсмены, Тренеры, Менеджеры)
                config = GROUP_MODEL_MAPPING[group.name]
                model_class = config['model']
                role = config.get('role')
                
                # Проверяем, есть ли уже запись для этого пользователя
                existing_record = model_class.objects.filter(user=user).first()
                
                if not existing_record:
                    # Создаем новую запись
                    if role:
                        # Для Staff с ролью и дефолтными значениями
                        from datetime import date
                        new_record = model_class.objects.create(
                            user=user, 
                            role=role,
                            birth_date=date(1990, 1, 1),  # Дефолтная дата
                            phone=f"+7{user.id:09d}",  # Дефолтный телефон
                        )
                    else:
                        # Для Parent, Athlete и Trainer без ролей
                        if model_class == Trainer:
                            # Для Trainer нужны обязательные поля
                            from datetime import date
                            new_record = model_class.objects.create(
                                user=user,
                                birth_date=date(1990, 1, 1),
                                phone=f"+7{user.id:09d}",
                            )
                        else:
                            new_record = model_class.objects.create(user=user)
                    
                    print(f"Создана запись {model_class.__name__} для пользователя {user.username} в группе {group.name}")
                    if role:
                        print(f"Назначена роль: {role}")
                    
                    # Логируем создание
                    AuditRecord.objects.create(
                        user=user,
                        action=f'create_{model_class.__name__.lower()}',
                        content_type=ContentType.objects.get_for_model(model_class),
                        object_id=new_record.id,
                        details=f"Автоматически создана запись {model_class.__name__} при добавлении в группу {group.name}" + (f" с ролью {role}" if role else "")
                    )
                else:
                    # Если запись уже существует, обновляем роль (только для Staff)
                    if isinstance(existing_record, Staff) and role:
                        if existing_record.role != role:
                            old_role = existing_record.role
                            existing_record.role = role
                            existing_record.save(update_fields=['role'])
                            print(f"Обновлена роль для {user.username}: {old_role} → {role}")
                            
                            # Логируем изменение роли
                            AuditRecord.objects.create(
                                user=user,
                                action='update_staff_role',
                                content_type=ContentType.objects.get_for_model(Staff),
                                object_id=existing_record.id,
                                details=f"Изменена роль с {old_role} на {role} при добавлении в группу {group.name}"
                            )
            else:
                # Для любой другой группы создаем Staff с ролью 'other'
                existing_staff = Staff.objects.filter(user=user).first()
                
                if not existing_staff:
                    # Создаем Staff для новой группы
                    from datetime import date
                    new_staff = Staff.objects.create(
                        user=user,
                        role='other',  # Дефолтная роль для новых групп
                        birth_date=date(1990, 1, 1),
                        phone=f"+7{user.id:09d}",
                    )
                    
                    print(f"Создана запись Staff для пользователя {user.username} в новой группе {group.name}")
                    
                    # Логируем создание
                    AuditRecord.objects.create(
                        user=user,
                        action='create_staff',
                        content_type=ContentType.objects.get_for_model(Staff),
                        object_id=new_staff.id,
                        details=f"Автоматически создана запись Staff при добавлении в новую группу {group.name} с ролью 'other'"
                    )
                else:
                    # Если Staff уже существует, обновляем роль на 'other' если она была другой
                    if existing_staff.role != 'other':
                        old_role = existing_staff.role
                        existing_staff.role = 'other'
                        existing_staff.save(update_fields=['role'])
                        print(f"Обновлена роль для {user.username}: {old_role} → other (новая группа {group.name})")
                        
                        # Логируем изменение роли
                        AuditRecord.objects.create(
                            user=user,
                            action='update_staff_role',
                            content_type=ContentType.objects.get_for_model(Staff),
                            object_id=existing_staff.id,
                            details=f"Изменена роль с {old_role} на 'other' при добавлении в новую группу {group.name}"
                        )

@receiver(m2m_changed, sender=User.groups.through)
def remove_role_records(sender, instance, action, pk_set, **kwargs):
    """Удаляет записи при удалении пользователя из группы (опционально)"""
    if action == "post_remove":  # При удалении из группы
        user = instance
        
        # Получаем удаленные группы
        removed_groups = Group.objects.filter(pk__in=pk_set)
        
        for group in removed_groups:
            if group.name in GROUP_MODEL_MAPPING:
                # Обработка специальных групп
                config = GROUP_MODEL_MAPPING[group.name]
                model_class = config['model']
                
                # Находим и удаляем запись
                existing_record = model_class.objects.filter(user=user).first()
                if existing_record:
                    existing_record.delete()
                    print(f"Удалена запись {model_class.__name__} для пользователя {user.username} из группы {group.name}")
                    
                    # Логируем удаление
                    AuditRecord.objects.create(
                        user=user,
                        action=f'delete_{model_class.__name__.lower()}',
                        content_type=ContentType.objects.get_for_model(model_class),
                        object_id=existing_record.id,
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
    if instance.role == 'manager':
        # Убираем из всех ролевых групп
        role_groups = Group.objects.filter(name__in=['Менеджеры'])
        for group in role_groups:
            instance.user.groups.remove(group)
        
        # Добавляем в нужную группу на основе роли
        if instance.role == 'manager':
            group = Group.objects.get_or_create(name='Менеджеры')[0]
            if instance.staff_role:
                group.permissions.set(instance.staff_role.permissions.all())
            instance.user.groups.add(group)

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
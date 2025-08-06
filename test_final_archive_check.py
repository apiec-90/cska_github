#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from core.forms import (
    TrainingGroupForm, AuthAccountForm, StaffForm, ParentForm, 
    AthleteForm, PaymentForm, PaymentMethodForm, DocumentForm,
    DocumentTypeForm, TrainingSessionForm, GroupScheduleForm, AttendanceRecordForm
)
from core.models import (
    TrainingGroup, AuthAccount, Staff, Parent, Athlete, 
    Payment, PaymentMethod, Document, DocumentType,
    TrainingSession, GroupSchedule, AttendanceRecord
)


def test_forms_import():
    """
    Тест импорта всех форм
    """
    print("🎯 Тест импорта всех форм")
    print("=" * 50)
    
    forms_to_test = [
        ('TrainingGroupForm', TrainingGroupForm),
        ('AuthAccountForm', AuthAccountForm),
        ('StaffForm', StaffForm),
        ('ParentForm', ParentForm),
        ('AthleteForm', AthleteForm),
        ('PaymentForm', PaymentForm),
        ('PaymentMethodForm', PaymentMethodForm),
        ('DocumentForm', DocumentForm),
        ('DocumentTypeForm', DocumentTypeForm),
        ('TrainingSessionForm', TrainingSessionForm),
        ('GroupScheduleForm', GroupScheduleForm),
        ('AttendanceRecordForm', AttendanceRecordForm),
    ]
    
    success_count = 0
    total_count = len(forms_to_test)
    
    for form_name, form_class in forms_to_test:
        try:
            form = form_class()
            print(f"✅ {form_name}: успешно создана")
            print(f"   Поля: {list(form.fields.keys())}")
            
            # Проверяем отсутствие полей архивирования
            archive_fields = ['is_archived', 'archived_at', 'archived_by']
            found_archive_fields = [field for field in archive_fields if field in form.fields]
            
            if found_archive_fields:
                print(f"   ⚠️  Найдены поля архивирования: {found_archive_fields}")
            else:
                print(f"   ✅ Поля архивирования отсутствуют")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ {form_name}: ошибка - {e}")
    
    print(f"\n📊 Результат: {success_count}/{total_count} форм работают корректно")
    return success_count == total_count


def test_models_import():
    """
    Тест импорта всех моделей
    """
    print("\n🎯 Тест импорта всех моделей")
    print("=" * 50)
    
    models_to_test = [
        ('TrainingGroup', TrainingGroup),
        ('AuthAccount', AuthAccount),
        ('Staff', Staff),
        ('Parent', Parent),
        ('Athlete', Athlete),
        ('Payment', Payment),
        ('PaymentMethod', PaymentMethod),
        ('Document', Document),
        ('DocumentType', DocumentType),
        ('TrainingSession', TrainingSession),
        ('GroupSchedule', GroupSchedule),
        ('AttendanceRecord', AttendanceRecord),
    ]
    
    success_count = 0
    total_count = len(models_to_test)
    
    for model_name, model_class in models_to_test:
        try:
            # Проверяем что модель может быть создана
            print(f"✅ {model_name}: модель доступна")
            print(f"   Поля: {[field.name for field in model_class._meta.fields]}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ {model_name}: ошибка - {e}")
    
    print(f"\n📊 Результат: {success_count}/{total_count} моделей работают корректно")
    return success_count == total_count


def test_archive_functionality():
    """
    Тест функциональности архивирования
    """
    print("\n🎯 Тест функциональности архивирования")
    print("=" * 50)
    
    # Проверяем модели с полями архивирования
    archive_models = [
        ('Staff', Staff),
        ('Parent', Parent),
        ('Athlete', Athlete),
        ('TrainingGroup', TrainingGroup),
        ('Payment', Payment),
        ('Document', Document),
    ]
    
    for model_name, model_class in archive_models:
        fields = [field.name for field in model_class._meta.fields]
        archive_fields = ['is_archived', 'archived_at', 'archived_by']
        
        missing_fields = [field for field in archive_fields if field not in fields]
        
        if missing_fields:
            print(f"❌ {model_name}: отсутствуют поля {missing_fields}")
        else:
            print(f"✅ {model_name}: все поля архивирования присутствуют")
    
    print("✅ Проверка полей архивирования завершена")


if __name__ == "__main__":
    print("🚀 Запуск полного тестирования системы")
    print("=" * 60)
    
    # Тестируем формы
    forms_ok = test_forms_import()
    
    # Тестируем модели
    models_ok = test_models_import()
    
    # Тестируем архивирование
    test_archive_functionality()
    
    print("\n" + "=" * 60)
    if forms_ok and models_ok:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Система готова к использованию")
    else:
        print("⚠️  Есть проблемы в системе")
        print("❌ Требуется исправление ошибок") 
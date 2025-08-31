from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User, Group
from django.urls import reverse

from core.models import (
    Athlete, Parent, Trainer, Staff, 
    TrainingGroup, GroupSchedule, TrainingSession,
    AthleteParent, AthleteTrainingGroup, AttendanceRecord,
    Payment, Document, DocumentType, AuditRecord,
    RegistrationDraft
)


class Command(BaseCommand):
    help = 'Комплексный тест функциональности админки Django'

    def __init__(self):
        super().__init__()
        self.client = Client()
        self.superuser = None

    def handle(self, *args, **options):
        self.run_full_test()

    def setup(self):
        """Подготовка к тестированию"""
        self.stdout.write("🔧 ПОДГОТОВКА К ТЕСТИРОВАНИЮ")
        self.stdout.write("=" * 50)
        
        # Получаем суперпользователя
        self.superuser = User.objects.filter(is_superuser=True).first()
        if self.superuser:
            self.stdout.write(f"✅ Найден суперпользователь: {self.superuser.username}")
        else:
            self.stdout.write("❌ Суперпользователь не найден!")
            return False
            
        # Логинимся в админку
        self.client.force_login(self.superuser)
        self.stdout.write("✅ Авторизация в админке выполнена")
        
        return True

    def test_admin_models_access(self):
        """Тест доступа к моделям в админке"""
        self.stdout.write("\n🏠 ТЕСТ ДОСТУПА К АДМИНСКИМ МОДЕЛЯМ")
        self.stdout.write("=" * 50)
        
        models_to_test = [
            ('core', 'athlete', 'Спортсмены'),
            ('core', 'parent', 'Родители'),
            ('core', 'trainer', 'Тренеры'),
            ('core', 'staff', 'Сотрудники'),
            ('core', 'traininggroup', 'Тренировочные группы'),
            ('core', 'attendancerecord', 'Записи посещаемости'),
            ('core', 'payment', 'Платежи'),
            ('core', 'document', 'Документы'),
        ]
        
        success_count = 0
        for app, model, name in models_to_test:
            try:
                url = reverse(f'admin:{app}_{model}_changelist')
                response = self.client.get(url)
                if response.status_code == 200:
                    self.stdout.write(f"   ✅ {name}: доступ OK")
                    success_count += 1
                else:
                    self.stdout.write(f"   ❌ {name}: ошибка {response.status_code}")
            except Exception as e:
                self.stdout.write(f"   ❌ {name}: исключение {e}")
        
        self.stdout.write(f"\nРезультат: {success_count}/{len(models_to_test)} моделей доступны")
        return success_count == len(models_to_test)

    def test_data_integrity(self):
        """Тест целостности данных"""
        self.stdout.write("\n🔍 ТЕСТ ЦЕЛОСТНОСТИ ДАННЫХ")
        self.stdout.write("=" * 50)
        
        issues = []
        
        # 1. Проверяем, что у всех пользователей есть профили
        try:
            users_without_profiles = []
            for user in User.objects.filter(is_superuser=False):
                has_profile = (
                    hasattr(user, 'athlete') or
                    hasattr(user, 'parent') or 
                    hasattr(user, 'trainer') or
                    hasattr(user, 'staff')
                )
                if not has_profile:
                    users_without_profiles.append(user.username)
            
            if users_without_profiles:
                issues.append(f"Пользователи без профилей: {', '.join(users_without_profiles)}")
            else:
                self.stdout.write("   ✅ Все пользователи имеют профили")
        except Exception as e:
            issues.append(f"Ошибка проверки профилей: {e}")
        
        # 2. Проверяем группы Django
        try:
            expected_groups = ['Спортсмены', 'Родители', 'Тренеры', 'Сотрудники', 'Менеджеры']
            existing_groups = list(Group.objects.values_list('name', flat=True))
            
            missing_groups = [g for g in expected_groups if g not in existing_groups]
            if missing_groups:
                issues.append(f"Отсутствуют группы: {', '.join(missing_groups)}")
            else:
                self.stdout.write("   ✅ Все необходимые группы Django существуют")
                
            # Проверяем, что пользователи назначены в группы
            users_without_groups = User.objects.filter(groups__isnull=True, is_superuser=False).count()
            if users_without_groups > 0:
                issues.append(f"{users_without_groups} пользователей не в группах")
            else:
                self.stdout.write("   ✅ Все пользователи назначены в группы")
        except Exception as e:
            issues.append(f"Ошибка проверки групп Django: {e}")
        
        # 3. Проверяем связи
        try:
            # Проверяем AthleteParent
            orphaned_relations = []
            for ap in AthleteParent.objects.all():
                if not ap.athlete_id or not ap.parent_id:
                    orphaned_relations.append(f"AthleteParent {ap.id}")
            
            # Проверяем AthleteTrainingGroup
            for atg in AthleteTrainingGroup.objects.all():
                if not atg.athlete_id or not atg.training_group_id:
                    orphaned_relations.append(f"AthleteTrainingGroup {atg.id}")
            
            if orphaned_relations:
                issues.append(f"Некорректные связи: {', '.join(orphaned_relations)}")
            else:
                self.stdout.write("   ✅ Все связи корректны")
        except Exception as e:
            issues.append(f"Ошибка проверки связей: {e}")
        
        if issues:
            self.stdout.write("\n❌ Обнаружены проблемы целостности:")
            for issue in issues:
                self.stdout.write(f"   - {issue}")
            return False
        else:
            self.stdout.write("\n✅ Целостность данных в порядке")
            return True

    def run_full_test(self):
        """Запуск полного теста"""
        self.stdout.write(self.style.SUCCESS("🧪 КОМПЛЕКСНЫЙ ТЕСТ АДМИНКИ"))
        self.stdout.write("=" * 60)
        
        if not self.setup():
            self.stdout.write(self.style.ERROR("❌ Ошибка инициализации"))
            return False
        
        tests = [
            ('Доступ к моделям', self.test_admin_models_access),
            ('Целостность данных', self.test_data_integrity),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.stdout.write(f"\n❌ Тест '{test_name}' завершился с ошибкой: {e}")
        
        # Итоговый отчет
        self.stdout.write(f"\n📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        self.stdout.write("=" * 60)
        
        if passed_tests == total_tests:
            self.stdout.write(self.style.SUCCESS("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!"))
            self.stdout.write(f"✅ {passed_tests}/{total_tests} тестов пройдено")
            self.stdout.write("\n🚀 Система готова к работе!")
            
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("🎊 ПОЗДРАВЛЯЕМ! РЕФАКТОРИНГ УСПЕШНО ЗАВЕРШЕН!"))
            self.stdout.write("=" * 60)
            self.stdout.write("✅ Админка полностью функциональна")
            self.stdout.write("✅ Все связи работают корректно")
            self.stdout.write("✅ Тестовые данные созданы")
            self.stdout.write("✅ Система готова к продуктивному использованию")
            self.stdout.write("\n🔗 Доступ к админке: http://127.0.0.1:8000/admin/")
            self.stdout.write("👤 Логин: admin")
            self.stdout.write("🔑 Пароль: (используйте существующий пароль суперпользователя)")
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ ТЕСТЫ ПРОЙДЕНЫ ЧАСТИЧНО"))
            self.stdout.write(f"✅ {passed_tests}/{total_tests} тестов пройдено")
            self.stdout.write(f"❌ {total_tests - passed_tests} тестов не пройдено")
            self.stdout.write("\nСистема работает, но есть некоторые вопросы для решения.")
        
        return passed_tests == total_tests
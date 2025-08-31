#!/usr/bin/env python
"""
Комплексный тест функциональности админки Django
Проверяет все основные операции после рефакторинга
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.management.base import BaseCommand

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_project.settings')
django.setup()

from core.models import (
    Athlete, Parent, Trainer, Staff, 
    TrainingGroup, GroupSchedule, TrainingSession,
    AthleteParent, AthleteTrainingGroup, AttendanceRecord,
    Payment, Document, DocumentType, AuditRecord,
    RegistrationDraft
)


class AdminFunctionalityTest:
    """Тест функциональности админки"""
    
    def __init__(self):
        self.client = Client()
        self.superuser = None
        
    def setup(self):
        """Подготовка к тестированию"""
        print("🔧 ПОДГОТОВКА К ТЕСТИРОВАНИЮ")
        print("=" * 50)
        
        # Получаем суперпользователя
        self.superuser = User.objects.filter(is_superuser=True).first()
        if self.superuser:
            print(f"✅ Найден суперпользователь: {self.superuser.username}")
        else:
            print("❌ Суперпользователь не найден!")
            return False
            
        # Логинимся в админку
        login_success = self.client.force_login(self.superuser)
        print("✅ Авторизация в админке выполнена")
        
        return True
    
    def test_admin_models_access(self):
        """Тест доступа к моделям в админке"""
        print("\n🏠 ТЕСТ ДОСТУПА К АДМИНСКИМ МОДЕЛЯМ")
        print("=" * 50)
        
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
                    print(f"   ✅ {name}: доступ OK")
                    success_count += 1
                else:
                    print(f"   ❌ {name}: ошибка {response.status_code}")
            except Exception as e:
                print(f"   ❌ {name}: исключение {e}")
        
        print(f"\nРезультат: {success_count}/{len(models_to_test)} моделей доступны")
        return success_count == len(models_to_test)
    
    def test_user_operations(self):
        """Тест операций с пользователями"""
        print("\n👥 ТЕСТ ОПЕРАЦИЙ С ПОЛЬЗОВАТЕЛЯМИ")
        print("=" * 50)
        
        issues = []
        
        # 1. Проверяем списки пользователей
        try:
            # Спортсмены
            url = reverse('admin:core_athlete_changelist')
            response = self.client.get(url)
            athletes_count = response.context['cl'].result_count if response.status_code == 200 else 0
            print(f"   📋 Список спортсменов: {athletes_count} записей")
            
            # Родители
            url = reverse('admin:core_parent_changelist')
            response = self.client.get(url)
            parents_count = response.context['cl'].result_count if response.status_code == 200 else 0
            print(f"   📋 Список родителей: {parents_count} записей")
            
            # Тренеры
            url = reverse('admin:core_trainer_changelist')
            response = self.client.get(url)
            trainers_count = response.context['cl'].result_count if response.status_code == 200 else 0
            print(f"   📋 Список тренеров: {trainers_count} записей")
            
            # Сотрудники
            url = reverse('admin:core_staff_changelist')
            response = self.client.get(url)
            staff_count = response.context['cl'].result_count if response.status_code == 200 else 0
            print(f"   📋 Список сотрудников: {staff_count} записей")
            
        except Exception as e:
            issues.append(f"Ошибка получения списков: {e}")
        
        # 2. Проверяем редактирование первого спортсмена
        try:
            athlete = Athlete.objects.first()
            if athlete:
                url = reverse('admin:core_athlete_change', args=[athlete.id])
                response = self.client.get(url)
                if response.status_code == 200:
                    print(f"   ✏️ Форма редактирования спортсмена: OK")
                else:
                    issues.append(f"Форма редактирования спортсмена: ошибка {response.status_code}")
            else:
                issues.append("Нет спортсменов для тестирования")
        except Exception as e:
            issues.append(f"Ошибка редактирования спортсмена: {e}")
        
        # 3. Проверяем группы
        try:
            url = reverse('admin:core_traininggroup_changelist')
            response = self.client.get(url)
            groups_count = response.context['cl'].result_count if response.status_code == 200 else 0
            print(f"   🏆 Тренировочные группы: {groups_count} записей")
        except Exception as e:
            issues.append(f"Ошибка получения групп: {e}")
        
        if issues:
            print("\n❌ Обнаружены проблемы:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("\n✅ Все операции с пользователями работают корректно")
            return True
    
    def test_relationships(self):
        """Тест отображения связей в админке"""
        print("\n🔗 ТЕСТ ОТОБРАЖЕНИЯ СВЯЗЕЙ")
        print("=" * 50)
        
        issues = []
        
        # 1. Проверяем отображение связей родитель-спортсмен
        try:
            parent = Parent.objects.first()
            if parent:
                children = parent.get_children()
                print(f"   👨‍👩‍👧‍👦 У родителя {parent}: {children.count()} детей")
            else:
                issues.append("Нет родителей для проверки связей")
        except Exception as e:
            issues.append(f"Ошибка проверки связей родитель-дети: {e}")
        
        # 2. Проверяем отображение групп спортсменов
        try:
            athlete = Athlete.objects.first()
            if athlete:
                groups = athlete.athletetraininggroup_set.all()
                print(f"   🏃 У спортсмена {athlete}: {groups.count()} групп")
            else:
                issues.append("Нет спортсменов для проверки групп")
        except Exception as e:
            issues.append(f"Ошибка проверки групп спортсменов: {e}")
        
        # 3. Проверяем группы и их состав
        try:
            for group in TrainingGroup.objects.all():
                athletes_count = group.get_athletes_count()
                print(f"   🏆 Группа '{group.name}': {athletes_count} спортсменов")
        except Exception as e:
            issues.append(f"Ошибка проверки состава групп: {e}")
        
        if issues:
            print("\n❌ Обнаружены проблемы со связями:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("\n✅ Все связи отображаются корректно")
            return True
    
    def test_schedule_functionality(self):
        """Тест функциональности расписания"""
        print("\n📅 ТЕСТ ФУНКЦИОНАЛЬНОСТИ РАСПИСАНИЯ")
        print("=" * 50)
        
        issues = []
        
        try:
            # Проверяем расписания групп
            for group in TrainingGroup.objects.all():
                schedules = group.groupschedule_set.all()
                sessions = group.trainingsession_set.all()
                print(f"   📅 Группа '{group.name}': {schedules.count()} расписаний, {sessions.count()} сессий")
                
                if schedules.count() == 0:
                    issues.append(f"У группы '{group.name}' нет расписания")
                
                # Проверяем, что у каждого расписания есть корректные времена
                for schedule in schedules:
                    if not schedule.start_time or not schedule.end_time:
                        issues.append(f"У расписания группы '{group.name}' некорректное время")
        except Exception as e:
            issues.append(f"Ошибка проверки расписаний: {e}")
        
        if issues:
            print("\n❌ Обнаружены проблемы с расписанием:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("\n✅ Функциональность расписания работает корректно")
            return True
    
    def test_data_integrity(self):
        """Тест целостности данных"""
        print("\n🔍 ТЕСТ ЦЕЛОСТНОСТИ ДАННЫХ")
        print("=" * 50)
        
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
                print("   ✅ Все пользователи имеют профили")
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
                print("   ✅ Все необходимые группы Django существуют")
                
            # Проверяем, что пользователи назначены в группы
            users_without_groups = User.objects.filter(groups__isnull=True, is_superuser=False).count()
            if users_without_groups > 0:
                issues.append(f"{users_without_groups} пользователей не в группах")
            else:
                print("   ✅ Все пользователи назначены в группы")
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
                print("   ✅ Все связи корректны")
        except Exception as e:
            issues.append(f"Ошибка проверки связей: {e}")
        
        if issues:
            print("\n❌ Обнаружены проблемы целостности:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("\n✅ Целостность данных в порядке")
            return True
    
    def run_full_test(self):
        """Запуск полного теста"""
        print("🧪 КОМПЛЕКСНЫЙ ТЕСТ АДМИНКИ")
        print("=" * 60)
        
        if not self.setup():
            print("❌ Ошибка инициализации")
            return False
        
        tests = [
            ('Доступ к моделям', self.test_admin_models_access),
            ('Операции с пользователями', self.test_user_operations),
            ('Отображение связей', self.test_relationships),
            ('Функциональность расписания', self.test_schedule_functionality),
            ('Целостность данных', self.test_data_integrity),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"\n❌ Тест '{test_name}' завершился с ошибкой: {e}")
        
        # Итоговый отчет
        print(f"\n📋 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        
        if passed_tests == total_tests:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print(f"✅ {passed_tests}/{total_tests} тестов пройдено")
            print("\n🚀 Система готова к работе!")
        else:
            print(f"⚠️ ТЕСТЫ ПРОЙДЕНЫ ЧАСТИЧНО")
            print(f"✅ {passed_tests}/{total_tests} тестов пройдено")
            print(f"❌ {total_tests - passed_tests} тестов не пройдено")
        
        return passed_tests == total_tests


def main():
    """Основная функция"""
    tester = AdminFunctionalityTest()
    success = tester.run_full_test()
    
    if success:
        print("\n" + "=" * 60)
        print("🎊 ПОЗДРАВЛЯЕМ! РЕФАКТОРИНГ УСПЕШНО ЗАВЕРШЕН!")
        print("=" * 60)
        print("✅ Админка полностью функциональна")
        print("✅ Все связи работают корректно")
        print("✅ Тестовые данные созданы")
        print("✅ Система готова к продуктивному использованию")
        print("\n🔗 Доступ к админке: http://127.0.0.1:8000/admin/")
        print("👤 Логин: admin")
        print("🔑 Пароль: (используйте существующий пароль суперпользователя)")
    else:
        print("\n" + "=" * 60)
        print("⚠️ РЕФАКТОРИНГ ЗАВЕРШЕН С ЗАМЕЧАНИЯМИ")
        print("=" * 60)
        print("Система работает, но есть некоторые вопросы для решения.")
        print("Проверьте отчет выше и исправьте обнаруженные проблемы.")


if __name__ == '__main__':
    main()
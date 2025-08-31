"""
Тесты администраторских интерфейсов Django.
Проверяют функциональность админок, форм и представлений.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.contrib.admin.sites import site
from unittest.mock import patch, MagicMock

from core.models import Trainer, Staff, Parent, Athlete, TrainingGroup
from core.admin.user_admins import TrainerAdmin, StaffAdmin, ParentAdmin, AthleteAdmin
from core.admin.group_admins import TrainingGroupAdmin
from core.admin.base import BasePersonAdmin, BaseDocumentMixin


class BasePersonAdminTest(TestCase):
    """Тесты базового класса админки пользователей"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Тест',
            last_name='Пользователь'
        )
        
        self.trainer = Trainer.objects.create(
            user=self.user,
            phone='+7 999 123 45 67',
            birth_date='1990-01-01',
            first_name='Иван',
            last_name='Петров'
        )
        
        # Создаем админа
        self.admin = TrainerAdmin(Trainer, site)
    
    def test_get_full_name_method(self):
        """Тест метода получения полного имени"""
        full_name = self.admin.get_full_name(self.trainer)
        self.assertEqual(full_name, 'Петров Иван')
    
    def test_get_full_name_fallback_to_user(self):
        """Тест фоллбэка к данным User"""
        # Создаем тренера без имени в профиле
        user2 = User.objects.create_user(
            username='testuser2',
            first_name='Юзер',
            last_name='Фамилия'
        )
        trainer2 = Trainer.objects.create(
            user=user2,
            phone='+7 999 111 22 33',
            birth_date='1990-01-01'
            # Не указываем first_name, last_name
        )
        
        full_name = self.admin.get_full_name(trainer2)
        self.assertEqual(full_name, 'Фамилия Юзер')
    
    def test_get_phone_method(self):
        """Тест метода получения телефона"""
        phone = self.admin.get_phone(self.trainer)
        self.assertEqual(phone, '+7 999 123 45 67')
    
    def test_get_active_status_method(self):
        """Тест метода получения статуса активности"""
        status = self.admin.get_active_status(self.trainer)
        self.assertEqual(status, 'Активен')
        
        # Деактивируем пользователя
        self.user.is_active = False
        self.user.save()
        
        status = self.admin.get_active_status(self.trainer)
        self.assertEqual(status, 'Неактивен')
    
    def test_queryset_optimization(self):
        """Тест оптимизации запросов"""
        # Мокаем request
        request = MagicMock()
        
        # Получаем оптимизированный queryset
        qs = self.admin.get_queryset(request)
        
        # Проверяем, что select_related('user') применен
        self.assertIn('user', str(qs.query))


class TrainerAdminTest(TestCase):
    """Тесты админки тренеров"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(
            username='trainer_test',
            email='trainer@test.com'
        )
        self.trainer = Trainer.objects.create(
            user=self.user,
            phone='+7 999 123 45 67',
            birth_date='1990-01-01'
        )
        
        # Создаем группу для тренера
        self.group = TrainingGroup.objects.create(
            name='Тестовая группа',
            age_min=10,
            age_max=15,
            trainer=self.trainer
        )
        
        self.admin = TrainerAdmin(Trainer, site)
    
    def test_get_groups_count(self):
        """Тест подсчета групп тренера"""
        count = self.admin.get_groups_count(self.trainer)
        self.assertEqual(count, 1)
    
    def test_get_groups_display(self):
        """Тест отображения групп тренера"""
        display = self.admin.get_groups_display(self.trainer)
        self.assertEqual(display, 'Тестовая группа')
        
        # Архивируем группу
        self.group.is_active = False
        self.group.save()
        
        display = self.admin.get_groups_display(self.trainer)
        self.assertEqual(display, 'Групп нет')


class StaffAdminTest(TestCase):
    """Тесты админки сотрудников"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(username='staff_test')
        self.staff = Staff.objects.create(
            user=self.user,
            role='manager',
            phone='+7 999 111 22 33',
            birth_date='1985-01-01'
        )
        
        self.admin = StaffAdmin(Staff, site)
    
    def test_get_role_display(self):
        """Тест отображения роли сотрудника"""
        role_display = self.admin.get_role_display(self.staff)
        self.assertEqual(role_display, 'Менеджер')


class AthleteAdminTest(TestCase):
    """Тесты админки спортсменов"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        # Спортсмен
        athlete_user = User.objects.create_user(username='athlete_test')
        self.athlete = Athlete.objects.create(
            user=athlete_user,
            birth_date='2010-01-01'
        )
        
        # Родитель
        parent_user = User.objects.create_user(
            username='parent_test',
            first_name='Родитель',
            last_name='Тестовый'
        )
        self.parent = Parent.objects.create(
            user=parent_user,
            birth_date='1980-01-01'
        )
        
        # Группа
        trainer_user = User.objects.create_user(username='trainer_for_athlete')
        trainer = Trainer.objects.create(
            user=trainer_user,
            phone='+7 999 555 66 77',
            birth_date='1990-01-01'
        )
        self.group = TrainingGroup.objects.create(
            name='Группа спортсмена',
            age_min=8,
            age_max=15,
            trainer=trainer
        )
        
        # Связи
        from core.models import AthleteParent, AthleteTrainingGroup
        AthleteParent.objects.create(athlete=self.athlete, parent=self.parent)
        AthleteTrainingGroup.objects.create(athlete=self.athlete, training_group=self.group)
        
        self.admin = AthleteAdmin(Athlete, site)
    
    def test_get_groups_display(self):
        """Тест отображения групп спортсмена"""
        display = self.admin.get_groups_display(self.athlete)
        self.assertEqual(display, 'Группа спортсмена')
    
    def test_get_parents_display(self):
        """Тест отображения родителей спортсмена"""
        display = self.admin.get_parents_display(self.athlete)
        self.assertEqual(display, 'Тестовый Родитель')


class ParentAdminTest(TestCase):
    """Тесты админки родителей"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        # Родитель
        parent_user = User.objects.create_user(
            username='parent_admin_test',
            first_name='Мама',
            last_name='Заботливая'
        )
        self.parent = Parent.objects.create(
            user=parent_user,
            birth_date='1975-01-01'
        )
        
        # Ребенок
        child_user = User.objects.create_user(
            username='child_test',
            first_name='Дитя',
            last_name='Милое'
        )
        self.child = Athlete.objects.create(
            user=child_user,
            birth_date='2012-01-01'
        )
        
        # Связь
        from core.models import AthleteParent
        AthleteParent.objects.create(athlete=self.child, parent=self.parent)
        
        self.admin = ParentAdmin(Parent, site)
    
    def test_get_children_display(self):
        """Тест отображения детей родителя"""
        display = self.admin.get_children_display(self.parent)
        self.assertEqual(display, 'Милое Дитя')


class TrainingGroupAdminTest(TestCase):
    """Тесты админки тренировочных групп"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        trainer_user = User.objects.create_user(username='group_trainer')
        self.trainer = Trainer.objects.create(
            user=trainer_user,
            phone='+7 999 777 88 99',
            birth_date='1990-01-01'
        )
        
        self.group = TrainingGroup.objects.create(
            name='Админ группа',
            age_min=10,
            age_max=16,
            trainer=self.trainer,
            max_athletes=20
        )
        
        self.admin = TrainingGroupAdmin(TrainingGroup, site)
    
    def test_get_age_range(self):
        """Тест отображения возрастного диапазона"""
        age_range = self.admin.get_age_range(self.group)
        self.assertEqual(age_range, '10-16 лет')
    
    def test_get_athletes_count_display(self):
        """Тест отображения количества спортсменов"""
        # Пустая группа
        count_display = self.admin.get_athletes_count(self.group)
        self.assertEqual(count_display, '0/20')


class DocumentMixinTest(TestCase):
    """Тесты миксина для работы с документами"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(username='doc_test')
        self.trainer = Trainer.objects.create(
            user=self.user,
            phone='+7 999 123 45 67',
            birth_date='1990-01-01'
        )
        
        # Создаем тип документа
        from core.models import DocumentType
        self.doc_type = DocumentType.objects.create(name='Тестовый документ')
    
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_file_path_processing(self, mock_open, mock_makedirs):
        """Тест обработки путей файлов"""
        mixin = BaseDocumentMixin()
        
        # Тестируем метод удаления физического файла
        test_paths = [
            '/media/avatars/test.jpg',
            'avatars/test.jpg',
            'http://example.com/media/avatars/test.jpg'
        ]
        
        for path in test_paths:
            # Не должно вызывать исключений
            mixin._delete_physical_file(path)


class AdminPermissionsTest(TestCase):
    """Тесты прав доступа в админке"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем группы пользователей
        self.managers_group = Group.objects.create(name='Менеджеры')
        self.trainers_group = Group.objects.create(name='Тренеры')
        
        # Создаем пользователей с разными ролями
        self.manager_user = User.objects.create_user(
            username='manager',
            password='testpass123',
            is_staff=True
        )
        self.manager_user.groups.add(self.managers_group)
        
        self.trainer_user = User.objects.create_user(
            username='trainer',
            password='testpass123',
            is_staff=True
        )
        self.trainer_user.groups.add(self.trainers_group)
        
        self.client = Client()
    
    def test_admin_access_with_permissions(self):
        """Тест доступа к админке с правами"""
        # Логинимся как менеджер
        self.client.login(username='manager', password='testpass123')
        
        # Пытаемся получить доступ к списку тренеров
        response = self.client.get('/admin/core/trainer/')
        
        # Проверяем, что получили ответ (не обязательно 200, зависит от прав)
        self.assertIn(response.status_code, [200, 302, 403])
    
    def test_admin_redirect_without_login(self):
        """Тест редиректа без авторизации"""
        response = self.client.get('/admin/core/trainer/')
        
        # Должен редиректить на страницу логина
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)


class AdminFormTest(TestCase):
    """Тесты форм в админке"""
    
    def test_sync_user_data_on_save(self):
        """Тест синхронизации данных с User при сохранении"""
        user = User.objects.create_user(username='sync_test')
        trainer = Trainer.objects.create(
            user=user,
            phone='+7 999 123 45 67',
            birth_date='1990-01-01',
            first_name='Новое',
            last_name='Имя'
        )
        
        admin = TrainerAdmin(Trainer, site)
        
        # Мокаем request и form
        request = MagicMock()
        form = MagicMock()
        
        # Сохраняем через админку
        admin.save_model(request, trainer, form, change=True)
        
        # Проверяем, что данные синхронизировались с User
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Новое')
        self.assertEqual(user.last_name, 'Имя')
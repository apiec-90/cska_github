from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Q
from datetime import date, datetime
from decimal import Decimal
from .models import (
    PaymentMethod, Staff, Parent, Athlete, TrainingGroup,
    AthleteTrainingGroup, AthleteParent, GroupSchedule,
    TrainingSession, AttendanceRecord, DocumentType,
    Document, Payment, AuditRecord
)
from .widgets import UserSearchWidget


class ModelRelationshipsTest(TestCase):
    """Тесты для проверки связей между моделями"""
    
    def setUp(self):
        """Создаем тестовые данные"""
        # Создаем пользователей
        self.user1 = User.objects.create_user(
            username='ivan_ivanov',
            first_name='Иван',
            last_name='Иванов',
            email='ivan@test.com'
        )
        
        self.user2 = User.objects.create_user(
            username='petr_petrov',
            first_name='Петр',
            last_name='Петров',
            email='petr@test.com'
        )
        
        self.user3 = User.objects.create_user(
            username='maria_sidorova',
            first_name='Мария',
            last_name='Сидорова',
            email='maria@test.com'
        )
        
        self.user4 = User.objects.create_user(
            username='vladimir_vladimirov',
            first_name='Владимир',
            last_name='Владимиров',
            email='vladimir@test.com'
        )
        
        # Создаем сотрудника (тренера)
        self.staff = Staff.objects.create(
            user=self.user1,
            phone='+7-999-123-45-67',
            birth_date=date(1980, 1, 1),
            description='Главный тренер'
        )
        
        # Создаем родителя
        self.parent = Parent.objects.create(
            user=self.user2
        )
        
        # Создаем спортсмена
        self.athlete = Athlete.objects.create(
            user=self.user3,
            birth_date=date(2010, 5, 15)
        )
        
        # Создаем тренировочную группу
        self.training_group = TrainingGroup.objects.create(
            name='Младшая группа',
            age_min=8,
            age_max=12,
            staff=self.staff,
            max_athletes=15
        )
        
        # Создаем способ оплаты
        self.payment_method = PaymentMethod.objects.create(
            name='Наличные'
        )
        
        # Создаем тип документа
        self.document_type = DocumentType.objects.create(
            name='Медицинская справка'
        )
    
    def test_staff_user_relationship(self):
        """Тест связи сотрудник-пользователь"""
        self.assertEqual(self.staff.user, self.user1)
        self.assertEqual(str(self.staff), 'Иван Иванов')
        self.assertEqual(self.staff.phone, '+7-999-123-45-67')
    
    def test_parent_user_relationship(self):
        """Тест связи родитель-пользователь"""
        self.assertEqual(self.parent.user, self.user2)
        self.assertEqual(str(self.parent), 'Петр Петров')
    
    def test_athlete_user_relationship(self):
        """Тест связи спортсмен-пользователь"""
        self.assertEqual(self.athlete.user, self.user3)
        self.assertEqual(str(self.athlete), 'Мария Сидорова')
        self.assertEqual(self.athlete.birth_date, date(2010, 5, 15))
    
    def test_athlete_parent_relationship(self):
        """Тест связи спортсмен-родитель"""
        # Создаем связь спортсмен-родитель
        athlete_parent = AthleteParent.objects.create(
            athlete=self.athlete,
            parent=self.parent
        )
        
        self.assertEqual(athlete_parent.athlete, self.athlete)
        self.assertEqual(athlete_parent.parent, self.parent)
        self.assertEqual(str(athlete_parent), 'Мария Сидорова - Петр Петров')
        
        # Проверяем метод получения родителей
        parents = self.athlete.get_parents()
        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0].parent, self.parent)
        
        # Проверяем отображение родителей
        parents_display = self.athlete.get_parents_display()
        self.assertEqual(parents_display, 'Петр Петров')
    
    def test_athlete_training_group_relationship(self):
        """Тест связи спортсмен-тренировочная группа"""
        # Создаем связь спортсмен-группа
        athlete_group = AthleteTrainingGroup.objects.create(
            athlete=self.athlete,
            training_group=self.training_group
        )
        
        self.assertEqual(athlete_group.athlete, self.athlete)
        self.assertEqual(athlete_group.training_group, self.training_group)
        self.assertEqual(str(athlete_group), 'Мария Сидорова - Младшая группа')
    
    def test_training_group_staff_relationship(self):
        """Тест связи тренировочная группа-сотрудник"""
        self.assertEqual(self.training_group.staff, self.staff)
        self.assertEqual(str(self.training_group), 'Младшая группа')
        self.assertEqual(self.training_group.age_min, 8)
        self.assertEqual(self.training_group.age_max, 12)
    
    def test_payment_relationships(self):
        """Тест связей в платежах"""
        payment = Payment.objects.create(
            athlete=self.athlete,
            training_group=self.training_group,
            payer=self.user4,
            amount=Decimal('5000.00'),
            payment_method=self.payment_method,
            billing_period_start=date(2025, 1, 1),
            billing_period_end=date(2025, 1, 31),
            is_automated=False,
            invoice_number='INV-001',
            created_by=self.staff
        )
        
        self.assertEqual(payment.athlete, self.athlete)
        self.assertEqual(payment.training_group, self.training_group)
        self.assertEqual(payment.payer, self.user4)
        self.assertEqual(payment.payment_method, self.payment_method)
        self.assertEqual(payment.created_by, self.staff)
        self.assertEqual(str(payment), 'INV-001')


class SearchFunctionalityTest(TestCase):
    """Тесты для проверки функциональности поиска"""
    
    def setUp(self):
        """Создаем тестовые данные для поиска"""
        # Создаем пользователей с разными именами
        self.user1 = User.objects.create_user(
            username='ivan_ivanov',
            first_name='Иван',
            last_name='Иванов',
            email='ivan@test.com'
        )
        
        self.user2 = User.objects.create_user(
            username='vladimir_vladimirov',
            first_name='Владимир',
            last_name='Владимиров',
            email='vladimir@test.com'
        )
        
        self.user3 = User.objects.create_user(
            username='vladislav_vladislavov',
            first_name='Владислав',
            last_name='Владиславов',
            email='vladislav@test.com'
        )
        
        self.user4 = User.objects.create_user(
            username='maria_marinova',
            first_name='Мария',
            last_name='Маринова',
            email='maria@test.com'
        )
        
        # Создаем пользователей с пустыми именами (должны исключаться)
        self.user5 = User.objects.create_user(
            username='empty_user',
            first_name='',
            last_name='',
            email='empty@test.com'
        )
    
    def test_user_search_widget_queryset(self):
        """Тест queryset виджета поиска пользователей"""
        widget = UserSearchWidget()
        queryset = widget.get_queryset()
        
        # Проверяем, что возвращаются только пользователи с именами
        self.assertIn(self.user1, queryset)
        self.assertIn(self.user2, queryset)
        self.assertIn(self.user3, queryset)
        self.assertIn(self.user4, queryset)
        
        # Проверяем, что пользователи с пустыми именами исключены
        self.assertNotIn(self.user5, queryset)
    
    def test_search_by_first_name(self):
        """Тест поиска по имени"""
        # Отладочная информация
        print(f"User1 first_name: '{self.user1.first_name}', last_name: '{self.user1.last_name}'")
        
        # Поиск по "Иван" (в правильном регистре)
        users = User.objects.filter(
            Q(first_name__icontains='Иван') |
            Q(last_name__icontains='Иван')
        )
        print(f"Found users: {list(users.values('first_name', 'last_name'))}")
        self.assertIn(self.user1, users)
    
    def test_search_by_last_name(self):
        """Тест поиска по фамилии"""
        # Отладочная информация
        print(f"User2 first_name: '{self.user2.first_name}', last_name: '{self.user2.last_name}'")
        
        # Поиск по "Владимиров" (в правильном регистре)
        users = User.objects.filter(
            Q(first_name__icontains='Владимиров') |
            Q(last_name__icontains='Владимиров')
        )
        print(f"Found users: {list(users.values('first_name', 'last_name'))}")
        self.assertIn(self.user2, users)
    
    def test_search_by_partial_name(self):
        """Тест поиска по части имени"""
        # Отладочная информация
        print(f"User2: '{self.user2.first_name}' '{self.user2.last_name}'")
        print(f"User3: '{self.user3.first_name}' '{self.user3.last_name}'")
        
        # Поиск по "Влад" (в правильном регистре, должен найти Владимир и Владислав)
        users = User.objects.filter(
            Q(first_name__icontains='Влад') |
            Q(last_name__icontains='Влад')
        )
        print(f"Found users: {list(users.values('first_name', 'last_name'))}")
        self.assertIn(self.user2, users)  # Владимир
        self.assertIn(self.user3, users)  # Владислав
    
    def test_search_by_maria(self):
        """Тест поиска по имени Мария"""
        # Отладочная информация
        print(f"User4 first_name: '{self.user4.first_name}', last_name: '{self.user4.last_name}'")
        
        users = User.objects.filter(
            Q(first_name__icontains='Мария') |
            Q(last_name__icontains='Мария')
        )
        print(f"Found users: {list(users.values('first_name', 'last_name'))}")
        self.assertIn(self.user4, users)


class AdminInterfaceTest(TestCase):
    """Тесты для проверки интерфейса админки"""
    
    def setUp(self):
        """Создаем суперпользователя для тестов админки"""
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')
    
    def test_admin_login(self):
        """Тест входа в админку"""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
    
    def test_athlete_admin_list(self):
        """Тест списка спортсменов в админке"""
        response = self.client.get('/admin/core/athlete/')
        self.assertEqual(response.status_code, 200)
    
    def test_staff_admin_list(self):
        """Тест списка сотрудников в админке"""
        response = self.client.get('/admin/core/staff/')
        self.assertEqual(response.status_code, 200)
    
    def test_parent_admin_list(self):
        """Тест списка родителей в админке"""
        response = self.client.get('/admin/core/parent/')
        self.assertEqual(response.status_code, 200)


class DataIntegrityTest(TestCase):
    """Тесты для проверки целостности данных"""
    
    def setUp(self):
        """Создаем тестовые данные"""
        self.user1 = User.objects.create_user(
            username='test_user1',
            first_name='Тест',
            last_name='Пользователь1'
        )
        
        self.user2 = User.objects.create_user(
            username='test_user2',
            first_name='Тест',
            last_name='Пользователь2'
        )
        
        self.staff = Staff.objects.create(
            user=self.user1,
            phone='+7-999-111-11-11',
            birth_date=date(1985, 1, 1)
        )
        
        self.parent = Parent.objects.create(
            user=self.user2
        )
        
        self.athlete = Athlete.objects.create(
            user=self.user1,
            birth_date=date(2010, 1, 1)
        )
    
    def test_unique_constraints(self):
        """Тест уникальных ограничений"""
        # Проверяем, что нельзя создать дублирующую связь спортсмен-родитель
        AthleteParent.objects.create(
            athlete=self.athlete,
            parent=self.parent
        )
        
        # Попытка создать дублирующую связь должна вызвать ошибку
        with self.assertRaises(Exception):
            AthleteParent.objects.create(
                athlete=self.athlete,
                parent=self.parent
            )
    
    def test_cascade_deletion(self):
        """Тест каскадного удаления"""
        # При удалении пользователя должны удаляться связанные записи
        user_count_before = User.objects.count()
        staff_count_before = Staff.objects.count()
        
        self.user1.delete()
        
        user_count_after = User.objects.count()
        staff_count_after = Staff.objects.count()
        
        self.assertEqual(user_count_after, user_count_before - 1)
        self.assertEqual(staff_count_after, staff_count_before - 1)


class SearchWidgetTest(TestCase):
    """Тесты для кастомного виджета поиска"""
    
    def test_widget_initialization(self):
        """Тест инициализации виджета"""
        widget = UserSearchWidget()
        self.assertIn('user-search-widget', widget.attrs['class'])
        self.assertIn('data-placeholder', widget.attrs)
    
    def test_widget_queryset_filtering(self):
        """Тест фильтрации queryset виджета"""
        # Создаем пользователей
        User.objects.create_user(
            username='user1',
            first_name='Иван',
            last_name='Иванов'
        )
        
        User.objects.create_user(
            username='user2',
            first_name='',
            last_name=''
        )
        
        widget = UserSearchWidget()
        queryset = widget.get_queryset()
        
        # Проверяем, что только пользователи с именами включены
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().username, 'user1')
    
    def test_widget_render(self):
        """Тест рендеринга виджета"""
        widget = UserSearchWidget()
        rendered = widget.render('test_field', None)
        
        # Проверяем, что в рендере есть JavaScript
        self.assertIn('user-search-input', rendered)
        self.assertIn('addEventListener', rendered)

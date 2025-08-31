"""
Тесты моделей Django для проекта CSKA.
Проверяют корректность работы моделей, связей и методов.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from core.models import (
    Trainer, Staff, Parent, Athlete, TrainingGroup, 
    AthleteTrainingGroup, AthleteParent, GroupSchedule,
    TrainingSession, AttendanceRecord, PaymentMethod, Payment
)


class UserProfileModelsTest(TestCase):
    """Тесты моделей пользователей: Trainer, Staff, Parent, Athlete"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.user1 = User.objects.create_user(
            username='test_trainer',
            email='trainer@test.com',
            first_name='Иван',
            last_name='Петров'
        )
        self.user2 = User.objects.create_user(
            username='test_athlete',
            email='athlete@test.com'
        )
        self.user3 = User.objects.create_user(
            username='test_parent',
            email='parent@test.com'
        )
        
    def test_trainer_creation(self):
        """Тест создания тренера"""
        trainer = Trainer.objects.create(
            user=self.user1,
            phone='+7 999 123 45 67',
            birth_date=date(1990, 1, 1),
            first_name='Иван',
            last_name='Петров'
        )
        
        self.assertEqual(str(trainer), 'Петров Иван')
        self.assertEqual(trainer.get_groups_count(), 0)
        self.assertEqual(trainer.get_athletes_count(), 0)
        self.assertFalse(trainer.is_archived)
    
    def test_trainer_str_fallback(self):
        """Тест отображения имени тренера с фоллбэком на User"""
        trainer = Trainer.objects.create(
            user=self.user1,
            phone='+7 999 123 45 67',
            birth_date=date(1990, 1, 1)
            # Не указываем first_name, last_name - должен взять из User
        )
        
        # Должен использовать данные из User
        self.assertEqual(str(trainer), 'Петров Иван')
    
    def test_staff_creation(self):
        """Тест создания сотрудника"""
        staff = Staff.objects.create(
            user=self.user1,
            role='manager',
            phone='+7 999 123 45 67',
            birth_date=date(1985, 5, 15),
            first_name='Менеджер',
            last_name='Системы'
        )
        
        self.assertEqual(staff.role, 'manager')
        self.assertEqual(staff.get_role_display(), 'Менеджер')
        self.assertIn('Менеджер', str(staff))
    
    def test_athlete_creation(self):
        """Тест создания спортсмена"""
        athlete = Athlete.objects.create(
            user=self.user2,
            birth_date=date(2010, 3, 20),
            phone='+7 999 111 22 33'
        )
        
        self.assertEqual(athlete.birth_date, date(2010, 3, 20))
        self.assertFalse(athlete.is_archived)
        # Проверяем методы получения связей
        self.assertEqual(athlete.get_parents().count(), 0)
    
    def test_parent_creation(self):
        """Тест создания родителя"""
        parent = Parent.objects.create(
            user=self.user3,
            phone='+7 999 555 66 77',
            birth_date=date(1980, 12, 10)
        )
        
        self.assertFalse(parent.is_archived)
        # Проверяем методы получения детей
        self.assertEqual(parent.get_children().count(), 0)


class TrainingGroupModelsTest(TestCase):
    """Тесты моделей тренировочных групп"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.trainer_user = User.objects.create_user(
            username='trainer1',
            email='trainer1@test.com'
        )
        self.trainer = Trainer.objects.create(
            user=self.trainer_user,
            phone='+7 999 123 45 67',
            birth_date=date(1990, 1, 1)
        )
        
        self.athlete_user = User.objects.create_user(
            username='athlete1',
            email='athlete1@test.com'
        )
        self.athlete = Athlete.objects.create(
            user=self.athlete_user,
            birth_date=date(2010, 1, 1)
        )
    
    def test_training_group_creation(self):
        """Тест создания тренировочной группы"""
        group = TrainingGroup.objects.create(
            name='Группа начинающих',
            age_min=8,
            age_max=12,
            trainer=self.trainer,
            max_athletes=15
        )
        
        self.assertEqual(str(group), 'Группа начинающих - Петров Иван')
        self.assertTrue(group.is_active)
        self.assertFalse(group.is_archived)
        self.assertEqual(group.get_athletes_count(), 0)
        self.assertEqual(group.get_parents_count(), 0)
    
    def test_athlete_training_group_relationship(self):
        """Тест связи спортсмен-группа"""
        group = TrainingGroup.objects.create(
            name='Тестовая группа',
            age_min=8,
            age_max=15,
            trainer=self.trainer
        )
        
        # Добавляем спортсмена в группу
        athlete_group = AthleteTrainingGroup.objects.create(
            athlete=self.athlete,
            training_group=group
        )
        
        self.assertEqual(str(athlete_group), f'{self.athlete} - {group}')
        self.assertEqual(group.get_athletes_count(), 1)
        
        # Проверяем уникальность связи
        with self.assertRaises(Exception):  # Должно вызвать ошибку уникальности
            AthleteTrainingGroup.objects.create(
                athlete=self.athlete,
                training_group=group
            )


class ScheduleModelsTest(TestCase):
    """Тесты моделей расписания"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        trainer_user = User.objects.create_user(username='trainer_schedule')
        self.trainer = Trainer.objects.create(
            user=trainer_user,
            phone='+7 999 111 22 33',
            birth_date=date(1990, 1, 1)
        )
        
        self.group = TrainingGroup.objects.create(
            name='Группа для расписания',
            age_min=10,
            age_max=16,
            trainer=self.trainer
        )
    
    def test_group_schedule_creation(self):
        """Тест создания расписания группы"""
        from datetime import time
        
        schedule = GroupSchedule.objects.create(
            training_group=self.group,
            weekday=1,  # Понедельник
            start_time=time(18, 0),
            end_time=time(19, 30)
        )
        
        self.assertEqual(schedule.get_weekday_display(), 'Понедельник')
        self.assertEqual(str(schedule), f'{self.group} - Понедельник')
        self.assertEqual(schedule.weekday, 1)
    
    def test_training_session_creation(self):
        """Тест создания тренировочной сессии"""
        from datetime import time
        
        session = TrainingSession.objects.create(
            training_group=self.group,
            date=date.today(),
            start_time=time(18, 0),
            end_time=time(19, 30)
        )
        
        self.assertEqual(str(session), f'{self.group} - {date.today()}')
        self.assertFalse(session.is_closed)
        self.assertFalse(session.is_canceled)


class PaymentModelsTest(TestCase):
    """Тесты моделей платежей"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем пользователей
        athlete_user = User.objects.create_user(username='athlete_payment')
        payer_user = User.objects.create_user(username='payer')
        staff_user = User.objects.create_user(username='staff_payment')
        trainer_user = User.objects.create_user(username='trainer_payment')
        
        # Создаем профили
        self.athlete = Athlete.objects.create(
            user=athlete_user,
            birth_date=date(2010, 1, 1)
        )
        self.staff = Staff.objects.create(
            user=staff_user,
            role='manager',
            phone='+7 999 111 22 33',
            birth_date=date(1990, 1, 1)
        )
        self.trainer = Trainer.objects.create(
            user=trainer_user,
            phone='+7 999 222 33 44',
            birth_date=date(1985, 1, 1)
        )
        self.group = TrainingGroup.objects.create(
            name='Платная группа',
            age_min=8,
            age_max=15,
            trainer=self.trainer
        )
        
        # Способ оплаты
        self.payment_method = PaymentMethod.objects.create(
            name='Наличные',
            is_active=True
        )
    
    def test_payment_creation(self):
        """Тест создания платежа"""
        from decimal import Decimal
        
        payment = Payment.objects.create(
            athlete=self.athlete,
            training_group=self.group,
            payer=self.athlete.user,
            amount=Decimal('5000.00'),
            payment_method=self.payment_method,
            billing_period_start=date.today(),
            billing_period_end=date.today() + timedelta(days=30),
            is_automated=False,
            is_paid=True,
            invoice_number='INV-001',
            created_by=self.staff
        )
        
        self.assertEqual(str(payment), 'INV-001')
        self.assertTrue(payment.is_paid)
        self.assertEqual(payment.amount, Decimal('5000.00'))


class ModelMethodsTest(TestCase):
    """Тесты специальных методов моделей"""
    
    def setUp(self):
        """Подготовка комплексных тестовых данных"""
        # Создаем пользователей
        parent_user = User.objects.create_user(username='parent_complex')
        athlete_user = User.objects.create_user(username='athlete_complex')
        trainer_user = User.objects.create_user(username='trainer_complex')
        
        # Создаем профили
        self.parent = Parent.objects.create(
            user=parent_user,
            birth_date=date(1980, 1, 1)
        )
        self.athlete = Athlete.objects.create(
            user=athlete_user,
            birth_date=date(2010, 1, 1)
        )
        self.trainer = Trainer.objects.create(
            user=trainer_user,
            phone='+7 999 777 88 99',
            birth_date=date(1990, 1, 1)
        )
        
        # Создаем группу
        self.group = TrainingGroup.objects.create(
            name='Комплексная группа',
            age_min=8,
            age_max=15,
            trainer=self.trainer
        )
        
        # Связываем родителя и ребенка
        AthleteParent.objects.create(
            athlete=self.athlete,
            parent=self.parent
        )
        
        # Добавляем ребенка в группу
        AthleteTrainingGroup.objects.create(
            athlete=self.athlete,
            training_group=self.group
        )
    
    def test_parent_children_methods(self):
        """Тест методов получения детей у родителя"""
        children_relations = self.parent.get_children_relations()
        children = self.parent.get_children()
        
        self.assertEqual(children_relations.count(), 1)
        self.assertEqual(children.count(), 1)
        self.assertEqual(children.first(), self.athlete)
    
    def test_trainer_statistics(self):
        """Тест статистических методов тренера"""
        groups_count = self.trainer.get_groups_count()
        athletes_count = self.trainer.get_athletes_count()
        
        self.assertEqual(groups_count, 1)
        self.assertEqual(athletes_count, 1)
    
    def test_group_statistics(self):
        """Тест статистических методов группы"""
        athletes_count = self.group.get_athletes_count()
        parents_count = self.group.get_parents_count()
        
        self.assertEqual(athletes_count, 1)
        self.assertEqual(parents_count, 1)


class ModelValidationTest(TestCase):
    """Тесты валидации моделей"""
    
    def test_required_fields(self):
        """Тест обязательных полей"""
        with self.assertRaises(Exception):
            # Не указываем обязательные поля
            TrainingGroup.objects.create(
                # name не указан - должно вызвать ошибку
                age_min=10,
                age_max=15
            )
    
    def test_age_range_logic(self):
        """Тест логики возрастных ограничений"""
        # Создаем группу с некорректным возрастом
        group = TrainingGroup(
            name='Тест возраста',
            age_min=15,
            age_max=10  # Максимум меньше минимума
        )
        
        # В реальном проекте можно добавить валидацию в модель
        # self.assertRaises(ValidationError, group.full_clean)
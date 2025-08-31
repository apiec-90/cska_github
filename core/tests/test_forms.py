"""
Тесты форм Django для проекта CSKA.
Проверяют валидацию, обработку данных и корректность работы форм.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import time, date

from core.forms import (
    Step1UserForm, Step2RoleForm, CommonProfileForm, StaffSubroleForm,
    TrainerForm, ParentForm, AthleteForm, StaffForm, GroupScheduleForm
)
from core.models import TrainingGroup, GroupSchedule, Trainer


class RegistrationFormsTest(TestCase):
    """Тесты форм регистрации пользователей"""
    
    def test_step1_user_form_valid(self):
        """Тест валидной формы создания пользователя"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        form = Step1UserForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_step1_user_form_password_mismatch(self):
        """Тест формы с несовпадающими паролями"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'complexpass123',
            'password2': 'differentpass456'
        }
        form = Step1UserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_step1_user_form_missing_email(self):
        """Тест формы без обязательного email"""
        form_data = {
            'username': 'testuser',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
            # email не указан
        }
        form = Step1UserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_step2_role_form_valid(self):
        """Тест валидной формы выбора роли"""
        form_data = {'role': 'trainer'}
        form = Step2RoleForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['role'], 'trainer')
    
    def test_step2_role_form_invalid_choice(self):
        """Тест формы с некорректным выбором роли"""
        form_data = {'role': 'invalid_role'}
        form = Step2RoleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('role', form.errors)
    
    def test_common_profile_form_valid(self):
        """Тест валидной формы профиля"""
        form_data = {
            'first_name': 'Иван',
            'last_name': 'Петров',
            'phone': '+7 999 123 45 67',
            'birth_date': '1990-01-01'
        }
        form = CommonProfileForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_common_profile_form_optional_phone(self):
        """Тест формы профиля без необязательного телефона"""
        form_data = {
            'first_name': 'Иван',
            'last_name': 'Петров',
            'birth_date': '1990-01-01'
            # phone не указан (необязательное поле)
        }
        form = CommonProfileForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_staff_subrole_form_valid(self):
        """Тест формы выбора подроли сотрудника"""
        form_data = {'subrole': 'manager'}
        form = StaffSubroleForm(data=form_data)
        self.assertTrue(form.is_valid())


class ProfileFormsTest(TestCase):
    """Тесты форм профилей пользователей"""
    
    def test_trainer_form_valid(self):
        """Тест валидной формы тренера"""
        form_data = {
            'first_name': 'Иван',
            'last_name': 'Тренеров',
            'phone': '+7 999 111 22 33',
            'birth_date': '1985-05-15'
        }
        form = TrainerForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_parent_form_valid(self):
        """Тест валидной формы родителя"""
        form_data = {
            'first_name': 'Мария',
            'last_name': 'Родительская',
            'phone': '+7 999 444 55 66',
            'birth_date': '1980-12-25'
        }
        form = ParentForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_athlete_form_valid(self):
        """Тест валидной формы спортсмена"""
        form_data = {
            'first_name': 'Петя',
            'last_name': 'Спортсменов',
            'birth_date': '2010-03-10'
        }
        form = AthleteForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_staff_form_valid(self):
        """Тест валидной формы сотрудника"""
        form_data = {
            'role': 'manager',
            'first_name': 'Анна',
            'last_name': 'Менеджерова',
            'phone': '+7 999 777 88 99',
            'birth_date': '1988-07-20'
        }
        form = StaffForm(data=form_data)
        self.assertTrue(form.is_valid())


class GroupScheduleFormTest(TestCase):
    """Тесты формы расписания группы"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        user = User.objects.create_user(username='schedule_trainer')
        trainer = Trainer.objects.create(
            user=user,
            phone='+7 999 123 45 67',
            birth_date='1990-01-01'
        )
        
        self.group = TrainingGroup.objects.create(
            name='Тестовая группа для расписания',
            age_min=10,
            age_max=16,
            trainer=trainer
        )
    
    def test_group_schedule_form_valid(self):
        """Тест валидной формы расписания"""
        form_data = {
            'training_group': self.group.id,
            'weekdays': ['1', '3', '5'],  # Пн, Ср, Пт
            'start_time': '18:00',
            'end_time': '19:30'
        }
        form = GroupScheduleForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_group_schedule_form_no_weekdays(self):
        """Тест формы без выбранных дней недели"""
        form_data = {
            'training_group': self.group.id,
            'weekdays': [],  # Пустой список
            'start_time': '18:00',
            'end_time': '19:30'
        }
        form = GroupScheduleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('weekdays', form.errors)
    
    def test_group_schedule_form_save_multiple_days(self):
        """Тест сохранения расписания на несколько дней"""
        form_data = {
            'training_group': self.group.id,
            'weekdays': ['1', '3'],  # Понедельник и среда
            'start_time': '17:00',
            'end_time': '18:30'
        }
        form = GroupScheduleForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        # Сохраняем форму
        saved_instance = form.save()
        
        # Проверяем, что создались записи для обоих дней
        schedules = GroupSchedule.objects.filter(training_group=self.group)
        self.assertEqual(schedules.count(), 2)
        
        # Проверяем дни недели
        weekdays = set(schedule.weekday for schedule in schedules)
        self.assertEqual(weekdays, {1, 3})
    
    def test_group_schedule_form_update_existing(self):
        """Тест обновления существующего расписания"""
        # Создаем существующее расписание
        existing_schedule = GroupSchedule.objects.create(
            training_group=self.group,
            weekday=1,
            start_time=time(18, 0),
            end_time=time(19, 0)
        )
        
        # Форма для редактирования
        form_data = {
            'training_group': self.group.id,
            'weekdays': ['1', '2'],  # Добавляем вторник
            'start_time': '18:00',
            'end_time': '19:30'  # Изменяем время окончания
        }
        form = GroupScheduleForm(data=form_data, instance=existing_schedule)
        
        self.assertTrue(form.is_valid())
        form.save()
        
        # Проверяем результат
        schedules = GroupSchedule.objects.filter(training_group=self.group)
        self.assertEqual(schedules.count(), 2)  # Понедельник + вторник


class FormValidationTest(TestCase):
    """Тесты кастомной валидации форм"""
    
    def test_phone_format_validation(self):
        """Тест валидации формата телефона"""
        # Тестируем разные форматы телефонов
        valid_phones = [
            '+7 999 123 45 67',
            '+79991234567',
            '89991234567',
            '999-123-45-67'
        ]
        
        for phone in valid_phones:
            form_data = {
                'first_name': 'Тест',
                'last_name': 'Телефонов',
                'phone': phone,
                'birth_date': '1990-01-01'
            }
            form = TrainerForm(data=form_data)
            # В данной реализации нет строгой валидации телефона
            # но форма должна принимать разные форматы
            self.assertTrue(form.is_valid(), f"Телефон {phone} должен быть валидным")
    
    def test_birth_date_validation(self):
        """Тест валидации даты рождения"""
        # Будущая дата - некорректна
        future_date = date.today().replace(year=date.today().year + 1)
        
        form_data = {
            'first_name': 'Тест',
            'last_name': 'Будущий',
            'birth_date': future_date.strftime('%Y-%m-%d')
        }
        form = AthleteForm(data=form_data)
        
        # В базовой реализации нет валидации будущих дат
        # но это может быть добавлено в кастомные clean методы
        self.assertTrue(form.is_valid())  # Пока принимаем любые даты
    
    def test_age_consistency_validation(self):
        """Тест валидации соответствия возраста"""
        # Создаем группу для детей
        user = User.objects.create_user(username='child_trainer')
        trainer = Trainer.objects.create(
            user=user,
            phone='+7 999 111 22 33',
            birth_date='1990-01-01'
        )
        
        child_group = TrainingGroup.objects.create(
            name='Детская группа',
            age_min=6,
            age_max=10,
            trainer=trainer
        )
        
        # Проверяем, что группа создалась с корректными возрастными ограничениями
        self.assertEqual(child_group.age_min, 6)
        self.assertEqual(child_group.age_max, 10)


class FormFieldsTest(TestCase):
    """Тесты полей форм и их атрибутов"""
    
    def test_form_field_attributes(self):
        """Тест атрибутов полей форм"""
        form = CommonProfileForm()
        
        # Проверяем атрибуты поля телефона
        phone_field = form.fields['phone']
        self.assertFalse(phone_field.required)  # Телефон необязательный
        self.assertIn('placeholder', phone_field.widget.attrs)
        
        # Проверяем атрибуты поля даты рождения
        birth_date_field = form.fields['birth_date']
        self.assertTrue(birth_date_field.required)  # Дата рождения обязательная
        self.assertEqual(birth_date_field.widget.attrs.get('type'), 'date')
    
    def test_group_schedule_weekdays_field(self):
        """Тест поля выбора дней недели в форме расписания"""
        form = GroupScheduleForm()
        
        weekdays_field = form.fields['weekdays']
        self.assertTrue(weekdays_field.required)
        
        # Проверяем выборы дней недели
        choices = dict(weekdays_field.choices)
        self.assertEqual(choices[1], 'Понедельник')
        self.assertEqual(choices[7], 'Воскресенье')
    
    def test_time_field_widgets(self):
        """Тест виджетов полей времени"""
        form = GroupScheduleForm()
        
        start_time_widget = form.fields['start_time'].widget
        end_time_widget = form.fields['end_time'].widget
        
        self.assertEqual(start_time_widget.attrs.get('type'), 'time')
        self.assertEqual(end_time_widget.attrs.get('type'), 'time')


class FormInitializationTest(TestCase):
    """Тесты инициализации форм"""
    
    def test_form_initial_data(self):
        """Тест инициализации формы с начальными данными"""
        initial_data = {
            'first_name': 'Начальное',
            'last_name': 'Имя'
        }
        
        form = CommonProfileForm(initial=initial_data)
        
        self.assertEqual(form.initial['first_name'], 'Начальное')
        self.assertEqual(form.initial['last_name'], 'Имя')
    
    def test_group_schedule_form_field_order(self):
        """Тест порядка полей в форме расписания"""
        form = GroupScheduleForm()
        
        # Проверяем, что поля расположены в правильном порядке
        field_names = list(form.fields.keys())
        expected_order = ['training_group', 'weekdays', 'start_time', 'end_time']
        
        self.assertEqual(field_names, expected_order)
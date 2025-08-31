"""
Тесты представлений Django для проекта CSKA.
Проверяют корректность работы views, обработку запросов и ответов.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from unittest.mock import patch

from core.models import RegistrationDraft, Trainer, Staff, Parent, Athlete
from core.views import (
    start_registration, step2_view, step3_view, 
    step4_view, cancel_registration, finish_registration
)


class RegistrationViewsTest(TestCase):
    """Тесты представлений регистрации пользователей"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.client = Client()
        
        # Создаем администратора для создания пользователей
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
    
    def test_start_registration_get(self):
        """Тест GET запроса к странице начала регистрации"""
        # Логинимся как администратор
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.get(reverse('start_registration'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'username')
        self.assertContains(response, 'email')
        self.assertContains(response, 'password1')
    
    def test_start_registration_post_valid(self):
        """Тест валидного POST запроса для создания пользователя"""
        self.client.login(username='admin', password='adminpass123')
        
        form_data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        
        response = self.client.post(reverse('start_registration'), data=form_data)
        
        # Проверяем редирект на шаг 2
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что пользователь создался
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Проверяем, что черновик создался
        self.assertTrue(RegistrationDraft.objects.filter(
            user__username='newuser'
        ).exists())
    
    def test_start_registration_cleanup_existing_draft(self):
        """Тест очистки существующего черновика при новой регистрации"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем существующий черновик
        old_user = User.objects.create_user(
            username='olduser',
            is_active=False
        )
        old_draft = RegistrationDraft.objects.create(
            user=old_user,
            created_by=self.admin_user,
            current_step=1
        )
        
        # Сохраняем ID в сессию
        session = self.client.session
        session['draft_id'] = old_draft.id
        session.save()
        
        # Начинаем новую регистрацию
        form_data = {
            'username': 'newuser2',
            'email': 'newuser2@test.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        
        response = self.client.post(reverse('start_registration'), data=form_data)
        
        # Проверяем, что старый черновик удалился
        self.assertFalse(RegistrationDraft.objects.filter(id=old_draft.id).exists())
        self.assertFalse(User.objects.filter(username='olduser').exists())
    
    def test_step2_role_selection(self):
        """Тест выбора роли на шаге 2"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем черновик
        user = User.objects.create_user(username='step2user', is_active=False)
        draft = RegistrationDraft.objects.create(
            user=user,
            created_by=self.admin_user,
            current_step=1
        )
        
        # GET запрос
        response = self.client.get(reverse('register_step2', args=[draft.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role')
        
        # POST запрос с выбором роли
        form_data = {'role': 'trainer'}
        response = self.client.post(
            reverse('register_step2', args=[draft.id]), 
            data=form_data
        )
        
        # Проверяем редирект на шаг 3
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что роль сохранилась
        draft.refresh_from_db()
        self.assertEqual(draft.role, 'trainer')
        self.assertEqual(draft.current_step, 2)
    
    def test_step3_profile_creation_trainer(self):
        """Тест создания профиля тренера на шаге 3"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем черновик с выбранной ролью тренера
        user = User.objects.create_user(username='traineruser', is_active=False)
        draft = RegistrationDraft.objects.create(
            user=user,
            created_by=self.admin_user,
            role='trainer',
            current_step=2
        )
        
        # POST запрос с данными профиля
        form_data = {
            'first_name': 'Иван',
            'last_name': 'Тренеров',
            'phone': '+7 999 123 45 67',
            'birth_date': '1990-01-01'
        }
        
        response = self.client.post(
            reverse('register_step3', args=[draft.id]), 
            data=form_data
        )
        
        # Проверяем редирект на страницу завершения
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что профиль тренера создался
        self.assertTrue(Trainer.objects.filter(user=user).exists())
        
        # Проверяем, что пользователь активирован
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        
        # Проверяем, что черновик завершен
        draft.refresh_from_db()
        self.assertTrue(draft.is_completed)
    
    def test_step3_profile_creation_staff_redirect_to_step4(self):
        """Тест создания профиля сотрудника с переходом к шагу 4"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем черновик с ролью сотрудника
        user = User.objects.create_user(username='staffuser', is_active=False)
        draft = RegistrationDraft.objects.create(
            user=user,
            created_by=self.admin_user,
            role='staff',
            current_step=2
        )
        
        form_data = {
            'first_name': 'Анна',
            'last_name': 'Менеджерова',
            'phone': '+7 999 777 88 99',
            'birth_date': '1985-05-15'
        }
        
        response = self.client.post(
            reverse('register_step3', args=[draft.id]), 
            data=form_data
        )
        
        # Для staff должен быть редирект на шаг 4 (выбор подроли)
        self.assertEqual(response.status_code, 302)
        self.assertIn('step4', response.url)
        
        # Проверяем, что базовый профиль Staff создался
        self.assertTrue(Staff.objects.filter(user=user).exists())
        
        # Пользователь пока не должен быть активирован
        user.refresh_from_db()
        self.assertFalse(user.is_active)
    
    def test_step4_staff_subrole_selection(self):
        """Тест выбора подроли сотрудника на шаге 4"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем черновик с ролью staff и профилем
        user = User.objects.create_user(username='staffuser4', is_active=False)
        draft = RegistrationDraft.objects.create(
            user=user,
            created_by=self.admin_user,
            role='staff',
            current_step=3
        )
        
        # Создаем базовый профиль Staff
        Staff.objects.create(
            user=user,
            role='other',  # Временная роль
            phone='+7 999 555 66 77',
            birth_date='1988-03-20'
        )
        
        # POST запрос с выбором подроли
        form_data = {'subrole': 'manager'}
        
        response = self.client.post(
            reverse('register_step4', args=[draft.id]), 
            data=form_data
        )
        
        # Проверяем редирект на страницу завершения
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что подроль установилась
        staff = Staff.objects.get(user=user)
        self.assertEqual(staff.subrole, 'manager')
        
        # Проверяем активацию пользователя
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        
        # Проверяем завершение черновика
        draft.refresh_from_db()
        self.assertTrue(draft.is_completed)
    
    def test_cancel_registration(self):
        """Тест отмены регистрации"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем черновик для отмены
        user = User.objects.create_user(username='canceluser', is_active=False)
        draft = RegistrationDraft.objects.create(
            user=user,
            created_by=self.admin_user,
            current_step=2
        )
        
        # Сохраняем ID в сессию
        session = self.client.session
        session['draft_id'] = draft.id
        session.save()
        
        # Отменяем регистрацию
        response = self.client.post(reverse('cancel_registration'))
        
        # Проверяем редирект
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что черновик и пользователь удалились
        self.assertFalse(RegistrationDraft.objects.filter(id=draft.id).exists())
        self.assertFalse(User.objects.filter(username='canceluser').exists())
        
        # Проверяем сообщение об отмене
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('отменена' in str(m) for m in messages))
    
    def test_finish_registration_page(self):
        """Тест страницы завершения регистрации"""
        response = self.client.get(reverse('register_done'))
        self.assertEqual(response.status_code, 200)


class RegistrationErrorHandlingTest(TestCase):
    """Тесты обработки ошибок в процессе регистрации"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
    
    def test_step2_with_invalid_draft_id(self):
        """Тест шага 2 с несуществующим ID черновика"""
        self.client.login(username='admin', password='adminpass123')
        
        # Пытаемся обратиться к несуществующему черновику
        response = self.client.get(reverse('register_step2', args=[99999]))
        
        # Должен быть редирект на шаг 1 с сообщением об ошибке
        self.assertEqual(response.status_code, 302)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('не найден' in str(m) for m in messages))
    
    def test_step3_without_role(self):
        """Тест шага 3 без выбранной роли"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем черновик без роли
        user = User.objects.create_user(username='noroleuser', is_active=False)
        draft = RegistrationDraft.objects.create(
            user=user,
            created_by=self.admin_user,
            current_step=1
            # role не указана
        )
        
        response = self.client.get(reverse('register_step3', args=[draft.id]))
        
        # Должен быть редирект на шаг 2
        self.assertEqual(response.status_code, 302)
        self.assertIn('step2', response.url)
    
    def test_step4_non_staff_access(self):
        """Тест доступа к шагу 4 не-сотрудником"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем черновик с ролью не-сотрудника
        user = User.objects.create_user(username='trainernotstaff', is_active=False)
        draft = RegistrationDraft.objects.create(
            user=user,
            created_by=self.admin_user,
            role='trainer',  # НЕ staff
            current_step=3
        )
        
        response = self.client.get(reverse('register_step4', args=[draft.id]))
        
        # Должен быть редирект на завершение или ошибка
        self.assertEqual(response.status_code, 302)


class ViewPermissionsTest(TestCase):
    """Тесты прав доступа к представлениям"""
    
    def setUp(self):
        self.client = Client()
        
        # Обычный пользователь без прав администратора
        self.regular_user = User.objects.create_user(
            username='regular',
            password='userpass123'
        )
    
    def test_registration_views_require_admin(self):
        """Тест требования прав администратора для регистрации"""
        # Без авторизации
        response = self.client.get(reverse('start_registration'))
        self.assertEqual(response.status_code, 302)  # Редирект на логин
        
        # С обычным пользователем
        self.client.login(username='regular', password='userpass123')
        response = self.client.get(reverse('start_registration'))
        self.assertEqual(response.status_code, 302)  # Нет прав доступа


class ViewDataIntegrityTest(TestCase):
    """Тесты целостности данных в представлениях"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
    
    @patch('core.utils.assign_groups_for_registration')
    def test_group_assignment_called(self, mock_assign_groups):
        """Тест вызова назначения групп при регистрации"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем черновик
        user = User.objects.create_user(username='groupuser', is_active=False)
        draft = RegistrationDraft.objects.create(
            user=user,
            created_by=self.admin_user,
            current_step=1
        )
        
        # Выбираем роль
        form_data = {'role': 'trainer'}
        response = self.client.post(
            reverse('register_step2', args=[draft.id]), 
            data=form_data
        )
        
        # Проверяем, что функция назначения групп была вызвана
        mock_assign_groups.assert_called_once_with(user, 'trainer')
    
    def test_user_activation_timing(self):
        """Тест правильного времени активации пользователя"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем черновик
        user = User.objects.create_user(username='activationuser', is_active=False)
        draft = RegistrationDraft.objects.create(
            user=user,
            created_by=self.admin_user,
            role='athlete',
            current_step=2
        )
        
        # На шаге 3 для обычных ролей пользователь должен активироваться
        form_data = {
            'first_name': 'Тест',
            'last_name': 'Активация',
            'birth_date': '2010-01-01'
        }
        
        response = self.client.post(
            reverse('register_step3', args=[draft.id]), 
            data=form_data
        )
        
        # Проверяем активацию
        user.refresh_from_db()
        self.assertTrue(user.is_active)


class SessionManagementTest(TestCase):
    """Тесты управления сессиями в процессе регистрации"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
    
    def test_draft_id_session_management(self):
        """Тест управления ID черновика в сессии"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем пользователя
        form_data = {
            'username': 'sessionuser',
            'email': 'session@test.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        
        response = self.client.post(reverse('start_registration'), data=form_data)
        
        # Проверяем, что draft_id сохранился в сессии
        self.assertIn('draft_id', self.client.session)
        
        draft_id = self.client.session['draft_id']
        self.assertTrue(RegistrationDraft.objects.filter(id=draft_id).exists())
    
    def test_session_cleanup_on_completion(self):
        """Тест очистки сессии при завершении регистрации"""
        self.client.login(username='admin', password='adminpass123')
        
        # Создаем черновик и проводим через весь процесс
        user = User.objects.create_user(username='cleanupuser', is_active=False)
        draft = RegistrationDraft.objects.create(
            user=user,
            created_by=self.admin_user,
            role='parent',
            current_step=2
        )
        
        # Устанавливаем в сессию
        session = self.client.session
        session['draft_id'] = draft.id
        session.save()
        
        # Завершаем регистрацию
        form_data = {
            'first_name': 'Родитель',
            'last_name': 'Завершающий',
            'birth_date': '1980-01-01'
        }
        
        response = self.client.post(
            reverse('register_step3', args=[draft.id]), 
            data=form_data
        )
        
        # Проверяем, что draft_id удалился из сессии
        self.assertNotIn('draft_id', self.client.session)
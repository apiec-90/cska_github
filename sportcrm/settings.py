import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

"""
Django settings for SportCRM project.
Настройки Django для проекта SportCRM.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Строим пути внутри проекта как BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: держите секретный ключ в тайне в продакшене!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-as4^0st8x+y_=!*1h75p7kxi^q!+0&0xqr-^lvw&nay4fyh85d')

# SECURITY WARNING: don't run with debug turned on in production!
# ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ: не запускайте с debug=True в продакшене!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Разрешенные хосты для приложения
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Application definition
# Определение приложений
INSTALLED_APPS = [
    # Встроенные приложения Django
    'django.contrib.admin',  # Административная панель
    'django.contrib.auth',   # Система аутентификации
    'django.contrib.contenttypes',  # Система типов контента
    'django.contrib.sessions',  # Система сессий
    'django.contrib.messages',  # Система сообщений
    'django.contrib.staticfiles',  # Обработка статических файлов
    
    # Сторонние приложения
    'tailwind',  # Интеграция с Tailwind CSS
    'sporttheme',  # Тема для спортивного CRM
    'theme',  # Дополнительная тема
    'django_browser_reload',  # Автоперезагрузка браузера при разработке
    'storages',  # Работа с облачными хранилищами
    
    # Собственные приложения
    'core',  # Основное приложение
    'groups',  # Управление группами
    'athletes',  # Управление спортсменами
    'attendance',  # Учет посещаемости
    'payments',  # Управление платежами
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_browser_reload.middleware.BrowserReloadMiddleware',
]

ROOT_URLCONF = 'sportcrm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'sportcrm.wsgi.application'

# Database
# Настройки базы данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Движок PostgreSQL
        'NAME': 'postgres',  # Имя базы данных
        'USER': 'postgres.gzrefdsqgynnvdodubiu',  # Пользователь базы данных
        'PASSWORD': os.getenv('DB_PASSWORD'),  # Пароль из переменных окружения
        'HOST': 'aws-0-eu-north-1.pooler.supabase.com',  # Хост Supabase
        'PORT': '6543',  # Порт подключения
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Интернационализация
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('ru', 'Russian'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Tailwind настройки
TAILWIND_APP_NAME = 'sporttheme'
INTERNAL_IPS = [
    "127.0.0.1",
]

NPM_BIN_PATH = BASE_DIR / "nodejs" / "npm.cmd"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

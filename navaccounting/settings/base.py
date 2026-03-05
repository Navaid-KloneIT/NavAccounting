import os
from pathlib import Path

import environ

env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    # Third party
    'allauth',
    'allauth.account',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'django_filters',
    'django_extensions',

    # Local apps
    'apps.core',
    'apps.tenants',
    'apps.accounts',
    'apps.roles',
    'apps.company',
    'apps.dashboard',
    'apps.general_ledger',
    'apps.accounts_payable',
    'apps.accounts_receivable',
    'apps.cash_management',
    'apps.fixed_assets',
    'apps.inventory',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'apps.tenants.middleware.TenantMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'navaccounting.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.tenants.context_processors.tenant_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'navaccounting.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Sites framework
SITE_ID = 1

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# django-allauth configuration
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_SIGNUP_REDIRECT_URL = '/tenants/select/'
LOGIN_REDIRECT_URL = '/tenants/select/'
LOGIN_URL = '/auth/login/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/auth/login/'
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_RATE_LIMITS = {'login_failed': '5/300s'}
ACCOUNT_ADAPTER = 'apps.accounts.adapters.NavAccountingAdapter'

# Crispy forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Session settings
SESSION_COOKIE_AGE = 86400 * 14  # 14 days
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True

# Email
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

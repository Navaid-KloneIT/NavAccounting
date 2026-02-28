from .base import *  # noqa: F401, F403

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

# Debug toolbar
INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405
INTERNAL_IPS = ['127.0.0.1']

# Email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

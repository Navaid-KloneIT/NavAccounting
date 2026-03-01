from .base import *  # noqa: F401, F403

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='navaccounting.db_backends.mysql'),  # noqa: F405
        'NAME': env('DB_NAME', default='navaccounting'),  # noqa: F405
        'USER': env('DB_USER', default='root'),  # noqa: F405
        'PASSWORD': env('DB_PASSWORD', default=''),  # noqa: F405
        'HOST': env('DB_HOST', default='localhost'),  # noqa: F405
        'PORT': env('DB_PORT', default='3306'),  # noqa: F405
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Debug toolbar (disabled — enable by uncommenting below)
# INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405
# INTERNAL_IPS = ['127.0.0.1']

# Email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

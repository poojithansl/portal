from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'systersdb',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

INTERNAL_IPS = ('127.0.0.1',)

# Uncomment the following for proper developing with DEBUG=False
# Possible scenarios are debugging custom error messages.
# SERVE_STATIC_OVERRIDE = True


# Instead of sending out real email, during development the emails will be sent
# to stdout, where from they can be inspected.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

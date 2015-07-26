from local_settings import *

DEBUG = False

ALLOWED_HOSTS = ['hvz.rucus.me', '46.101.29.8', '127.0.0.1']

ADMINS = (
    ('Administrator', 'admin@rucus.me'),
)

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'uchicagohvz',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# REST framework settings
REST_FRAMEWORK = {
	'DEFAULT_RENDERER_CLASSES': (
		'rest_framework.renderers.JSONRenderer',
	)
}

# Email settings
EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
CELERY_EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

try:
    from secrets import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
except:
    EMAIL_HOST_USER = 'placeholder'
    EMAIL_HOST_PASSWORD = 'placeholder'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
MAIL_USE_TLS = True

# Chat settings
CHAT_SERVER_URL = 'https://hvz.rucus.me/chat'
CHAT_ADMIN_URL = 'https://hvz.rucus.me/admin'

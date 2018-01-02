from local_settings import *

DEBUG = False 

ALLOWED_HOSTS = ['www.uchicagohvz.org']

ADMINS = (
    ('Administrator', 'admin@uchicagohvz.org'),
)
SERVER_EMAIL = 'noreply@uchicagohvz.org'

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
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = os.environ.get('EMAIL_PORT', '')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = True
MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', '')
MAILING_LIST_TEST_RECIPIENTS = os.environ.get('MAILING_LIST_TEST_RECIPIENTS', '').split(',')
SMTP_UCHICAGO_USER = os.environ.get('SMTP_UCHICAGO_USER', '')
SMTP_UCHICAGO_PASSWORD = os.environ.get('SMTP_UCHICAGO_PASSWORD', '')

# Chat settings
CHAT_SERVER_URL = '//www.uchicagohvz.org/chat'

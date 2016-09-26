"""
Django settings for uchicagohvz project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(__file__)

RECAPTCHA_USE_SSL = True

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
try:
    from secrets import SECRET_KEY
except:
    SECRET_KEY = 'SECRET KEY PLACEHOLDER'
try:
    from secrets import RECAPTCHA_PUBLIC_KEY
except:
    RECAPTCHA_PUBLIC_KEY = 'PUBLIC KEY PLACEHOLDER'
try:
    from secrets import RECAPTCHA_PRIVATE_KEY
except:
    RECAPTCHA_PRIVATE_KEY = 'PRIVATE KEY PLACEHOLDER'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []



# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mptt', 'localflavor', 'djcelery_email', 'compressor', 'rest_framework', 'captcha', 'django_redis',
    'uchicagohvz.users', 'uchicagohvz.game',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
TEMPLATE_CONTEXT_PROCESSORS += 'django.core.context_processors.request',


ROOT_URLCONF = 'uchicagohvz.urls'

WSGI_APPLICATION = 'uchicagohvz.wsgi.application'


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Chicago'

USE_I18N = False

USE_L10N = False

USE_TZ = True

# Templates
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, "templates"),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

# Django Compressor
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder'
)

COMPRESS_PRECOMPILERS = (
    ('text/coffeescript', 'coffee -bcs'),
    ('text/less', 'lessc {infile} {outfile}'),
)
COMPRESS_ROOT = os.path.join(BASE_DIR, 'static')

# Datetime settings
DATETIME_FORMAT = 'N j, Y g:i A'
SHORT_DATETIME_FORMAT = 'm/d/Y g:i A'

# User-uploaded media
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# Authentication
AUTHENTICATION_BACKENDS = (
    'uchicagohvz.users.backend.UChicagoLDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)
LOGIN_URL = "/users/login/?required=true"
LOGIN_REDIRECT_URL = "/"

# Caching and sessions
KEY_PREFIX = 'uchicagohvz'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': '127.0.0.1:11211'
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_HTTPONLY = False # required for reading sessionid cookie in chat JS

# HTTPS settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')

# Message framework settings
from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: 'info',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger'
} # Bootstrap 3 alert integration

# Celery configuration
BROKER_URL = 'redis://localhost:6379/3'

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'UChicago HvZ <noreply@uchicagohvz.org>'
SYMPA_FROM_EMAIL = 'admin@uchicagohvz.org'
SYMPA_TO_EMAIL = 'sympa@lists.uchicago.edu'

# HvZ game configuration
HUMAN_KILL_POINTS = 1 # how many points killing a human is worth
HVT_KILL_POINTS = 3 # default points a high-value target is worth (replaces regular human kill points)
HVT_AWARD_POINTS = 0 # default award points a human gets for being an HVT and surviving
HVD_KILL_POINTS = 3 # default points a target from a high-value dorm is worth (can stack on top of HVT points)
LEADERBOARD_CACHE_DURATION = 3600 # how many seconds to cache certain DB-intensive leaderboard queries
NEXMO_NUMBER = '979-476-7025'
GAME_SW_BOUND = (41.783985, -87.606053)
GAME_NE_BOUND = (41.798128, -87.584016)

# Dealer settings
TEMPLATE_CONTEXT_PROCESSORS += 'dealer.contrib.django.staff.context_processor',
DEALER_PATH = os.path.dirname(BASE_DIR)

# Chat settings
CHAT_SERVER_URL = 'http://192.168.1.20:36452/chat'
CHAT_ADMIN_URL = 'http://localhost:36452/admin/'

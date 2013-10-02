from local_settings import *

REST_FRAMEWORK = {
	'DEFAULT_RENDERER_CLASSES': (
		'rest_framework.renderers.JSONRenderer',
	)
}

# Mandrill email settings
EMAIL_HOST = 'smtp.mandrillapp.com'
from secrets import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
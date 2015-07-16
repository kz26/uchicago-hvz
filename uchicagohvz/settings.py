from production_settings import *
DEBUG = True
try:
    from secrets import DATABASES
except:
    DATABASES = {
    	'default': {
    		'ENGINE': 'django.db.backends.sqlite3',
    		'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    	}
    }

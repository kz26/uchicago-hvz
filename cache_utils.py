from django.core.cache import cache
from django.conf import settings
from hashlib import sha256

def cache_func(seconds):
	def dec(f):
		def inner(*args, **kwargs):
			key = sha256("%s%s%s%s" % (f.__module__, f.__name__, args, kwargs)).hexdigest()
			result = cache.get(key)
			if result is None or settings.DEBUG:
				result = f(*args, **kwargs)
				cache.set(key, result, seconds)
			return result
		return inner
	return dec

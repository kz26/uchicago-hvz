from django.core.cache import cache
from django.conf import settings
from hashlib import sha256

def cache_func(seconds):
	def dec(f):
		def inner(*args, **kwargs):
			use_cache = kwargs.pop('use_cache', True)
			key = "%s%s%s%s" % (f.__module__, f.__name__, args, kwargs)
			key_hash = sha256(key).hexdigest()
			result = cache.get(key_hash)
			if result is None or settings.DEBUG or use_cache == False:
				result = f(*args, **kwargs)
				cache.set(key_hash, result, seconds)
			return result
		return inner
	return dec

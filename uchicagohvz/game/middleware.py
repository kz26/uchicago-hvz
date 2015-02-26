from django.core.urlresolvers import resolve, reverse, Resolver404
from django.http import HttpResponseRedirect
from django.utils import timezone
from datetime import datetime

class Feb262015Middleware(object):
	target_url = 'feb-26-2015-charlie-hebdo'
	
	def process_request(self, request):
		try:
			rm = resolve(request.path)
			if rm.url_name == self.target_url:
				return None
		except Resolver404:
			pass
		start_dt = datetime(2015, 2, 26, 6, tzinfo=timezone.get_default_timezone())
		end_dt = datetime(2015, 2, 26, 23, 59, 59, tzinfo=timezone.get_default_timezone())
		if start_dt <= timezone.now() <= end_dt:
			return HttpResponseRedirect(reverse(self.target_url))
		return None
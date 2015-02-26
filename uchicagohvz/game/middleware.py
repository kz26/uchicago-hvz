from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone
from datetime import datetime

class Feb262015Middleware(object):
	def process_request(self, request):
		start_dt = datetime(2015, 2, 26, 6, tzinfo=timezone.get_default_timezone())
		end_dt = datetime(2015, 2, 26, 23, 59, 59, tzinfo=timezone.get_default_timezone())
		if start_dt <= timezone.now() <= end_dt:
			return HttpResponseRedirect(reverse('feb-26-2015-charlie-hebdo'))
		return None
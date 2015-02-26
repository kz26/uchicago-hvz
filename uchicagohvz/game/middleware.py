from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.contrib import messages
from datetime import datetime

class Feb262015Middleware(object):

	msg_content = mark_safe("""
	<p>IMPORTANT: Gameplay will be suspended February 26th from 6am-11:59pm.
	<a class="alert-link" href="/feb-26-2015/">Read the bulletin</a> for more details.</p>
	""")
	
	def process_request(self, request):
		if request.path != '/feb-26-2015/':
			start_dt = datetime(2015, 2, 26, 6, tzinfo=timezone.get_default_timezone())
			end_dt = datetime(2015, 2, 26, 23, 59, 59, tzinfo=timezone.get_default_timezone())
			if start_dt <= timezone.now() <= end_dt:
				return HttpResponseRedirect('/feb-26-2015/')
			elif timezone.now() < start_dt:
				messages.error(request, self.msg_content)
		else:
			return None
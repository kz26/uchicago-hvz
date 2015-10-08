# Mailing list configuration

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from . import tasks
from .models import Profile

from rest_framework.views import APIView

import email
import hashlib
import hmac


def _verify(token, timestamp, signature):
	return signature == hmac.new(
							 key=settings.MAILGUN_API_KEY,
							 msg='{}{}'.format(timestamp, token),
							 digestmod=hashlib.sha256).hexdigest()

class ChatterMailgunHook(APIView):

	@method_decorator(csrf_exempt)
	def post(self, request, *args, **kwargs):
		if all([x in request.data for x in (
			'recipient', 'sender', 'from',
			'subject', 'body-mime',
			'timestamp', 'token', 'signature'
			)
		]) and _verify(request.data['token'], request.data['timestamp'], request.data['signature']):
			msg = email.message_from_string(request.data['body-mime'])
			for x in ('From', 'Sender', 'To', 'Reply-To', 'Subject'):
				del msg[x]
			msg['From'] = request.data['from']
			msg['Sender'] = 'chatter@lists.uchicagohvz.org'
			msg['To'] = msg['Sender']
			msg['Reply-To'] = msg['Sender']
			msg['Subject'] = "[HvZ-Chatter] " + request.data['subject']
			to_addrs = list(Profile.objects.filter(
				user__active=True, subscribe_chatter_listhost=True).values_list('user__email', flat=True))
			tasks.smtp_localhost_send_raw(msg['Sender'], to_addrs, msg.as_string())


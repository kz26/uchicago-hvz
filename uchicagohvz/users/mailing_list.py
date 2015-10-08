# Mailing list configuration

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from uchicagohvz import secrets
from .tasks import smtp_localhost_send
from .models import Profile

from rest_framework.response import Response
from rest_framework.views import APIView

import email
import hashlib
import hmac


def _verify(token, timestamp, signature):
	return signature == hmac.new(
							 key=secrets.MAILGUN_API_KEY,
							 msg='{}{}'.format(timestamp, token),
							 digestmod=hashlib.sha256).hexdigest()

class ChatterMailgunHook(APIView):

	authentication_classes = []

	@method_decorator(csrf_exempt)
	def post(self, request, *args, **kwargs):
		FIELDS = (
			'recipient', 'sender', 'from',
			'subject', 'body-mime',
			'timestamp', 'token', 'signature'
		)
		verified = _verify(request.data['token'], request.data['timestamp'], request.data['signature'])
		if all([x in request.data for x in FIELDS]) and verified:
			msg = email.message_from_string(request.data['body-mime'])
			for x in ('From', 'Sender', 'To', 'Reply-To', 'Subject'):
				del msg[x]
			listhost_addr = 'chatter@lists.uchicagohvz.org'
			msg['From'] = request.data['from']
			msg['Sender'] = listhost_addr
			msg['To'] = listhost_addr
			msg['Reply-To'] = listhost_addr
			msg['Subject'] = "[HvZ-Chatter] " + request.data['subject']
			to_addrs = tuple(Profile.objects.filter(
				user__is_active=True, subscribe_chatter_listhost=True).values_list('user__email', flat=True))
			smtp_localhost_send(msg['Sender'], to_addrs, msg.as_string())
			return Response()
		else:
			return Response(status=406) 

# Mailing list configuration

from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from uchicagohvz import secrets
from .tasks import smtp_localhost_send
from .models import Profile

from rest_framework.response import Response
from rest_framework.views import APIView

import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
			msg['Subject'] = request.data['subject']
			if '[HvZ-Chatter]' not in msg['Subject']:
				msg['Subject'] = '[HvZ-Chatter] ' + msg['Subject']
			msg['List-Id'] = 'HvZ-Chatter <https://www.uchicagohvz.org>'
			msg['List-Unsubscribe'] = '<https://www.uchicagohvz.org/users/update_profile/>'
			include_unsub = True 
			for p in msg.walk():
				if p.get_filename('') == 'how_to_unsubscribe.txt':
					include_unsub = False
					break
			if include_unsub:
				unsub_p = MIMEText(render_to_string('users/emails/how_to_unsubscribe.txt'), 'plain')
				unsub_p.add_header('Content-Disposition', 'inline', filename='how_to_unsubscribe.txt')
				if msg.is_multipart():
					if msg.get_content_type() == 'multipart/alternative':
						msg_a = msg.get_payload()
						msg.set_type('multipart/mixed')
						msg_a_p = MIMEMultipart('alternative')
						msg_a_p.set_payload(msg_a)
						msg.set_payload(msg_a_p)
					msg.attach(unsub_p)
				elif msg.get_content_maintype() == 'text':
					subtype = msg.get_content_subtype()
					text_p = MIMEText(msg.get_payload(), subtype, msg.get_content_charset('us-ascii'))
					msg.set_type('multipart/mixed')
					msg.set_payload([text_p, unsub_p])
			to_addrs = tuple(Profile.objects.filter(
				user__is_active=True, subscribe_chatter_listhost=True).values_list('user__email', flat=True))
			smtp_localhost_send(listhost_addr, to_addrs, msg.as_string())
			return Response()
		else:
			return Response(status=406) 

from celery import task
from django.conf import settings
from django.core import mail

@task
def do_sympa_update(user, listname, subscribe):
	if subscribe:
		body = "QUIET ADD %s %s %s" % (listname, user.email, user.get_full_name())
	else:
		body = "QUIET DELETE %s %s" % (listname, user.email)
	email = mail.EmailMessage(subject='', body=body, from_email=settings.SYMPA_FROM_EMAIL, to=[settings.SYMPA_TO_EMAIL])
	email.send()

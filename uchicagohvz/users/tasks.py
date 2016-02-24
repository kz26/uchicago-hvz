from celery import task
from django.conf import settings
from django.core import mail

from uchicagohvz import secrets

import smtplib


@task
def do_sympa_update(user, listname, subscribe):
	if subscribe:
		body = "QUIET ADD %s %s %s" % (listname, user.email, user.get_full_name())
	else:
		body = "QUIET DELETE %s %s" % (listname, user.email)
	email = mail.EmailMessage(subject='', body=body, from_email=settings.SYMPA_FROM_EMAIL, to=[settings.SYMPA_TO_EMAIL])
	email.send()


@task
def smtp_localhost_send(from_addr, to_addrs, msg):
	# send using localhost SMTP
	server = smtplib.SMTP('localhost')
	server.sendmail(from_addr, to_addrs, msg)
	server.quit()


@task
def smtp_uchicago_send(from_addr, to_addrs, msg):
	# send using UChicago authenticated SMTP
	server = smtplib.SMTP_SSL('authsmtp.uchicago.edu')
	server.login(secrets.UCHICAGO_SMTP_USER, secrets.UCHICAGO_SMTP_PASSWORD)
	server.sendmail(from_addr, to_addrs, msg)
	server.quit()
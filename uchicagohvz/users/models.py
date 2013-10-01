from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from localflavor.us.models import PhoneNumberField
from uchicagohvz.users.phone import CARRIERS

# Create your models here.

class Profile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL)
	phone_number = PhoneNumberField(blank=True)
	phone_carrier = models.CharField(max_length=32, blank=True, choices=[(x[0], x[0]) for x in CARRIERS])
	subscribe_death_notifications = models.BooleanField(default=False)
	subscribe_chatter_listhost = models.BooleanField(default=True)

	def __unicode__(self):
		return self.user.get_full_name()

	@models.permalink
	def get_absolute_url(self):
		return ("users|profile",)

def get_or_create_profile(sender, **kwargs):
	profile, created = Profile.objects.get_or_create(user=kwargs['instance'])
	if created:
		pass # do email signup here

models.signals.post_save.connect(get_or_create_profile, sender=get_user_model())
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from localflavor.us.models import PhoneNumberField

# Create your models here.

class Profile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL)
	phone_number = PhoneNumberField(blank=True) 
	subscribe_chatter_listhost = models.BooleanField(default=True)

	def __unicode__(self):
		return self.user.get_full_name()

def get_or_create_profile(sender, **kwargs):
	profile, created = Profile.objects.get_or_create(user=kwargs['instance'])
	if created:
		pass # do email signup here

models.signals.post_save.connect(get_or_create_profile, sender=get_user_model())
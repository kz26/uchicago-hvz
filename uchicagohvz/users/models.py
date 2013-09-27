from django.db import models
from django.conf import settings
from localflavor.us.models import PhoneNumberField

# Create your models here.

class Profile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL)
	phone_number = PhoneNumberField(blank=True) 
	subscribe_chatter_listhost = models.BooleanField(default=True)

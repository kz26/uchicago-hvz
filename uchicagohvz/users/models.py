from django.db import models
from django.conf import settings
from django.contrib.auth.models import User 
from localflavor.us.models import PhoneNumberField
from uchicagohvz.users.phone import CARRIERS

# Create your models here.

class Profile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL)
	phone_number = PhoneNumberField(blank=True)
	phone_carrier = models.CharField(max_length=32, blank=True, choices=[(k, k) for k in sorted(CARRIERS.keys())])
	last_words = models.CharField(max_length=255, blank=True)
	subscribe_death_notifications = models.BooleanField(default=False)
	subscribe_chatter_listhost = models.BooleanField(default=True)
	subscribe_zombies_listhost = models.BooleanField(default=True)
	subscribe_zombie_texts = models.BooleanField(default=False)

	def __unicode__(self):
		return self.user.get_full_name()

	@models.permalink
	def get_absolute_url(self):
		return ("users|update_profile",)

def get_or_create_profile(sender, **kwargs):
	if not kwargs.get('raw'):
		profile, created = Profile.objects.get_or_create(user=kwargs['instance'])
		if created:
			from uchicagohvz.users.tasks import do_sympa_update
			do_sympa_update.delay(profile.user, 'hvz-chatter', True)
			do_sympa_update.delay(profile.user, 'zombies', True)
models.signals.post_save.connect(get_or_create_profile, sender=User)

def sympa_update(sender, **kwargs):
	if not kwargs.get('raw'):
		from uchicagohvz.users.tasks import do_sympa_update
		try:
			old_profile = Profile.objects.get(id=kwargs['instance'].id)
		except:
			return
		new_profile = kwargs['instance']
		user = new_profile.user
		if (not old_profile.subscribe_chatter_listhost) and new_profile.subscribe_chatter_listhost:
			do_sympa_update.delay(user, 'hvz-chatter', True)
		elif old_profile.subscribe_chatter_listhost and (not new_profile.subscribe_chatter_listhost):
			do_sympa_update.delay(user, 'hvz-chatter', False)
		
		if (not old_profile.subscribe_zombies_listhost) and new_profile.subscribe_zombies_listhost:
			do_sympa_update.delay(user, 'zombies', True)
		elif old_profile.subscribe_zombies_listhost and (not new_profile.subscribe_zombies_listhost):
			do_sympa_update.delay(user, 'zombies', False)

models.signals.pre_save.connect(sympa_update, sender=Profile)

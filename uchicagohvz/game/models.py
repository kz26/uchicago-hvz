from django.db import models
from django.conf import settings
from django.utils import timezone
from uchicagohvz.overwrite_fs import OverwriteFileSystemStorage
from uchicagohvz.users.backend import UChicagoLDAPBackend
from mptt.models import MPTTModel, TreeForeignKey

import os
import random

# Create your models here.

def gen_rules_filename(instance, fn):
	return "rules/%s%s" % (instance.name, os.path.splitext(fn)[1])

class Game(models.Model):
	class Meta:
		ordering = ['-start_date']

	name = models.CharField(max_length=255)
	registration_date = models.DateTimeField()
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	rules = models.FileField(upload_to=gen_rules_filename, storage=OverwriteFileSystemStorage())
	terms = models.TextField()

	def __unicode__(self):
		return self.name

	@property
	def status(self):
		now = timezone.now()
		if self.registration_date < now < self.start_date:
			return "registration"
		elif self.start_date < now < self.end_date:
			return "in_progress"
		elif now > self.end_date:
			return "finished"
		else:
			return "inactive"


DORMS = (
	("BS", "Blackstone"),
	("BR", "Breckinridge"),
	("BV", "Broadview"),
	("BJ", "Burton-Judson Courts"),
	("IH", "International House"),
	("MC", "Maclean"),
	("MAX", "Max Palevsky"),
	("NG", "New Graduate Residence Hall"),
	("SH", "Snell-Hitchcock"),
	("SC", "South Campus"),
	("ST", "Stony Island"),
	("OFF", "Off campus")
)

NOUNS = open(os.path.join(settings.BASE_DIR, "game/word-lists/nouns.txt")).read().split('\n')[:-1]
ADJECTIVES = open(os.path.join(settings.BASE_DIR, "game/word-lists/adjs.txt")).read().split('\n')[:-1]

def gen_bite_code():
	return random.choice(ADJECTIVES) + " " + random.choice(NOUNS)

class Player(models.Model):
	class Meta:
		unique_together = (("user", "game"), ("game", "bite_code"))
		ordering = ['user__last_name']

	user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+")
	game = models.ForeignKey(Game, related_name="players")
	active = models.BooleanField(default=False)
	bite_code = models.CharField(max_length=255, blank=True, help_text="leave blank for automatic (re-)generation")
	dorm = models.CharField(max_length=4, choices=DORMS)
	major = models.CharField(max_length=255, editable=False)
	human = models.BooleanField(default=True)
	points = models.IntegerField(default=0)

	def save(self, *args, **kwargs):
		old = None
		if not self.id:
			self.major = UChicagoLDAPBackend.get_user_major(self.user.username)
		else:
			old = Player.objects.get(id=self.id)
		if (old and (not old.active) and self.active) or (old is None and self.active) or self.bite_code == "":
			# generate unique bite code
			while True:
				bc = gen_bite_code()
				if not Player.objects.filter(game=self.game, bite_code=bc).exists():
					self.bite_code = bc
					break
		super(Player, self).save(*args, **kwargs)

	def __unicode__(self):
		return self.user.get_full_name()

class Kill(MPTTModel):
	class MPTTMeta:
		order_insertion_by = ['date']

	parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
	killer = models.ForeignKey(Player, related_name="+")
	victim = models.ForeignKey(Player, related_name="+")
	date = models.DateTimeField()

class Award(models.Model):
	game = models.ForeignKey(Game, related_name="+")
	name = models.CharField(max_length=255)
	points = models.IntegerField()
	players = models.ManyToManyField(Player, related_name="awards")
	code = models.CharField(max_length=255)
	redeem_limit = models.IntegerField(default=0)

class HighValueTarget(models.Model):
	player = models.OneToOneField(Player)
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	points = models.IntegerField()

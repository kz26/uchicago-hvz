from django.db import models
from django.conf import settings
from django.utils import timezone
from uchicagohvz.overwrite_fs import OverwriteFileSystemStorage
from mptt.models import MPTTModel, TreeForeignKey

import os

# Create your models here.

def gen_rules_filename(fn):
	return "rules/%s%s" % (name, os.path.splitext(fn)[1])

class Game(models.Model):
	class Meta:
		ordering = ['-start_date']

	name = models.CharField(max_length=255)
	registration_date = models.DateTimeField()
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	rules = models.FileField(upload_to=gen_rules_filename, storage=OverwriteFileSystemStorage())

class Player(models.Model):
	class Meta:
		unique_together = ("user", "game")

	user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+")
	game = models.ForeignKey(Game, related_name="players")
	active = models.BooleanField(default=False)
	bite_code = models.CharField(max_length=255)
	is_human = models.CharField(max_length=255)
	points = models.IntegerField(default=0)

class Kill(MPTTModel):
	parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
	killer = models.ForeignKey(Player, related_name="+")
	victim = models.ForeignKey(Player, related_name="+")
	date = models.DateTimeField(auto_now_add=True)

class Award(models.Model):
	game = models.ForeignKey(Game, related_name="+")
	name = models.CharField(max_length=255)
	points = models.IntegerField()
	players = models.ManyToManyField(Player, related_name="awards")
	code = models.CharField(max_length=255)
	redeem_limit = models.IntegerField(default=0)
from django.db import models
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from uchicagohvz.overwrite_fs import OverwriteFileSystemStorage
from uchicagohvz.users.backend import UChicagoLDAPBackend
from mptt.models import MPTTModel, TreeForeignKey

import hashlib
import os
import random

# Create your models here.

def gen_rules_filename(instance, fn):
	return "rules/%s%s" % (instance.name, os.path.splitext(fn)[1])

class GameManager(models.Manager):
	def games_in_progress(self):
		now = timezone.now()
		return self.filter(start_date__lte=now, end_date__gte=now)

class Game(models.Model):
	class Meta:
		ordering = ['-start_date']

	name = models.CharField(max_length=255)
	registration_date = models.DateTimeField()
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	rules = models.FileField(upload_to=gen_rules_filename, storage=OverwriteFileSystemStorage())
	
	objects = GameManager()

	def __unicode__(self):
		return self.name

	def get_registered_players(self):
		return self.players.all()

	def get_active_players(self):
		return self.players.filter(active=True)

	def get_humans(self):
		return self.get_active_players().filter(human=True)

	def get_zombies(self):
		return self.get_active_players().filter(human=False)

	def get_players_in_dorm(self, dorm):
		return self.get_active_players().filter(dorm=dorm)

	@property
	def status(self):
		now = timezone.now()
		if self.registration_date < now < self.start_date:
			return 'registration'
		elif self.start_date < now < self.end_date:
			return 'in_progress'
		elif now > self.end_date:
			return 'finished'
		else:
			return 'future'

	@models.permalink
	def get_absolute_url(self):
		return ('game|show', [self.pk])

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
	return random.choice(ADJECTIVES) + ' ' + random.choice(NOUNS)

class Player(models.Model):
	class Meta:
		unique_together = (('user', 'game'), ('game', 'bite_code'))
		ordering = ['-game__start_date', 'user__username', 'user__last_name', 'user__first_name']

	user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
	game = models.ForeignKey(Game, related_name='players')
	active = models.BooleanField(default=False)
	bite_code = models.CharField(max_length=255, blank=True, help_text='leave blank for automatic (re-)generation')
	dorm = models.CharField(max_length=4, choices=DORMS)
	major = models.CharField(max_length=255, editable=False)
	human = models.BooleanField(default=True)
	points = models.IntegerField(default=0)
	renting_gun = models.BooleanField(default=False)
	gun_returned = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		if self.game.status == 'registration': # allow updates to major during registration
			backend = UChicagoLDAPBackend()
			self.major = backend.get_user_major(self.user.username)
		if not self.bite_code:
			# (re-)generate unique bite code
			while True:
				bc = gen_bite_code()
				if not Player.objects.filter(game=self.game, bite_code=bc).exists() and not Award.objects.filter(game=self.game, code=bc).exists():
					self.bite_code = bc
					break
		old = Player.objects.get(id=self.id) if self.id else None
		if (old and (not old.active) and self.active): # if user was newly activated
			profile = self.user.profile
			profile.subscribe_zombies_listhost = True # force subscription to zombies listhost
			profile.save()
		super(Player, self).save(*args, **kwargs)

	@property
	def killed_by(self):
		try:
			return Kill.objects.filter(victim__game=self.game).order_by('-date').get(victim=self).killer
		except Kill.DoesNotExist:
			return None

	@property
	def kills(self):
		return Kill.objects.filter(killer__id=self.id).exclude(victim__id=self.id).order_by('-date')

	@transaction.atomic
	def kill_me(self, killer):
		if not self.human:
			return None
		self.human = False
		self.save()
		parent_kills = Kill.objects.filter(victim=killer).order_by('-date')
		if parent_kills.exists():
			parent_kill = parent_kills[0]
		else:
			parent_kill = None
		points = settings.HUMAN_KILL_POINTS
		tags = []
		now = timezone.now()
		try:
			hvt = HighValueTarget.objects.get(player=self)
			if hvt.start_date < now < hvt.end_date:
				points = hvt.points
				tags.append("HVT")
		except HighValueTarget.DoesNotExist:
			pass
		try:
			hvd = HighValueDorm.objects.get(game=self.game, dorm=self.dorm)
			if hvd.start_date < now < hvd.end_date:
				points += hvd.points
				tags.append("HVD")
		except HighValueDorm.DoesNotExist:
			pass
		tagtxt = ", ".join(tags)
		return Kill.objects.create(parent=parent_kill, killer=killer, victim=self, points=points, notes=tagtxt, date=now)

	@property
	def display_name(self): # real name when game is over; otherwise, dorm + obfuscated code for humans and bite code for zombies
		if self.game.status == "in_progress":
			if self.human:
				return "%s %s" % (self.get_dorm_display(), hashlib.sha256(self.bite_code).hexdigest()[:2].upper())
			else:
				return self.bite_code
		else:
			return self.user.get_full_name()

	@property
	def human_points(self):
		return self.awards.filter(redeem_type__in=('H', 'A')).aggregate(points=models.Sum('points'))['points'] or 0

	@property
	def zombie_points(self):
		kill_points = Kill.objects.exclude(parent=None, killer=self, victim=self).filter(killer=self).aggregate(points=models.Sum('points'))['points'] or 0
		award_points =  self.awards.filter(redeem_type__in=('Z', 'A')).aggregate(points=models.Sum('points'))['points'] or 0
		return kill_points + award_points

	def __unicode__(self):
		return "%s - %s - %s (%s)" % (self.user.username, self.user.get_full_name(), self.bite_code, self.game.name)

class Kill(MPTTModel):
	class Meta:
		ordering = ['-date']
	class MPTTMeta:
		order_insertion_by = ['date']

	parent = TreeForeignKey('self', null=True, blank=True, related_name='children', editable=False)
	killer = models.ForeignKey(Player, related_name="+")
	victim = models.ForeignKey(Player, related_name="+")
	date = models.DateTimeField(default=timezone.now)
	points = models.IntegerField(default=settings.HUMAN_KILL_POINTS)
	notes = models.TextField(blank=True)
	lat = models.FloatField(null=True, blank=True, verbose_name='latitude')
	lng = models.FloatField(null=True, blank=True, verbose_name='longitude')

	def __unicode__(self):
		return "%s (%s) --> %s (%s) [%s]" % (self.killer.user.get_full_name(), self.killer.user.username, self.victim.user.get_full_name(), self.victim.user.username, self.killer.game.name)

	def save(self, *args, **kwargs):
		try:
			parent = Kill.objects.exclude(id=self.id).get(victim=self.killer)
		except Kill.DoesNotExist:
			parent = None
		self.parent = parent
		super(Kill, self).save(*args, **kwargs)

REDEEM_TYPES = (
	('H', 'Humans only'),
	('Z', 'Zombies only'),
	('A', 'All players'),
)

class Award(models.Model):
	class Meta:
		unique_together = (('game', 'name'), ('game', 'code'))
	
	game = models.ForeignKey(Game, related_name='+')
	name = models.CharField(max_length=255)
	points = models.IntegerField(help_text='Can be negative, e.g. to penalize players')
	players = models.ManyToManyField(Player, related_name='awards', null=True, blank=True, help_text='Players that should receive this award.')
	code = models.CharField(max_length=255, blank=True, help_text='leave blank for automatic (re-)generation')
	redeem_limit = models.IntegerField(help_text='Maximum number of players that can redeem award via code entry (set to 0 for moderator-added awards/points)')
	redeem_type = models.CharField(max_length=1, choices=REDEEM_TYPES)

	def __unicode__(self):
		return "%s (%s)" % (self.name, self.game.name)

	def save(self, *args, **kwargs):
		if not self.code:
			while True:
				code = gen_bite_code()
				if not Award.objects.filter(game=self.game, code=code).exists() and not Player.objects.filter(game=self.game, bite_code=code).exists():
					self.code = code
					break
		super(Award, self).save(*args, **kwargs)

class HighValueTarget(models.Model):
	player = models.OneToOneField(Player, unique=True)
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	points = models.IntegerField(default=settings.HVT_KILL_POINTS)

	def __unicode__(self):
		return "%s" % (self.player)

class HighValueDorm(models.Model):
	class Meta:
		unique_together = ('game', 'dorm')
	game = models.ForeignKey(Game)
	dorm = models.CharField(max_length=4, choices=DORMS)
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	points = models.IntegerField(default=settings.HVD_KILL_POINTS)

	def __unicode__(self):
		return "%s (%s)" % (self.get_dorm_display(), self.game.name)

def update_score(sender, **kwargs):
	players = []
	if sender == Kill:
		players = [kwargs['instance'].killer.id]
	elif sender == Award.players.through:
		if kwargs['action'] in ('post_add', 'post_remove'):
			players = kwargs.get('pk_set')
			if players is None:
				return
		elif kwargs['action'] == 'post_clear':
			players = Player.objects.filter(active=True, game=kwargs['instance'].game).values_list('id', flat=True)
		else:
			return
	elif sender == Award:
		players = Player.objects.filter(active=True, game=kwargs['instance'].game).values_list('id', flat=True)
	for pid in players:
		p = Player.objects.get(pk=pid)
		kill_points = Kill.objects.filter(killer=p).exclude(victim=p).aggregate(points=models.Sum('points'))['points'] or 0
		award_points = p.awards.aggregate(points=models.Sum('points'))['points'] or 0
		p.points = kill_points + award_points
		p.save(update_fields=['points'])

models.signals.post_save.connect(update_score, sender=Kill)
models.signals.post_delete.connect(update_score, sender=Kill)
models.signals.m2m_changed.connect(update_score, sender=Award.players.through)
models.signals.post_delete.connect(update_score, sender=Award)

def unzombify(sender, **kwargs):
	victim = kwargs['instance'].victim
	if not Kill.objects.filter(victim=victim).exists():
		victim.human = True
		victim.save()

models.signals.post_delete.connect(unzombify, sender=Kill)


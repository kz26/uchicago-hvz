from __future__ import division
from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import Q
from django.template import defaultfilters
from django.utils import timezone

from uchicagohvz.overwrite_fs import OverwriteFileSystemStorage
from uchicagohvz.users.backend import UChicagoLDAPBackend

from mptt.models import MPTTModel, TreeForeignKey
from ranking import Ranking

import hashlib
import os
import random


# Create your models here.

def gen_rules_filename(instance, fn):
	return "rules/%s%s" % (instance.name, os.path.splitext(fn)[1])

def gen_pics_filename(instance, fn):
	return "pictures/%s%s" % (instance.picture.url, os.path.splitext(fn)[1])

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
	picture = models.FileField(upload_to=gen_pics_filename, storage=OverwriteFileSystemStorage(), null=True, blank=True)
	color = models.CharField(max_length=64, default="#FFFFFF")	
	flavor = models.TextField(max_length=6000, default="")


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

	def get_kills(self):
		"""
		Return all Kill objects for this game
		"""
		return Kill.objects.filter(killer__game=self)

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

	@property
	def humans_listhost_address(self):
		return "%s-humans@lists.uchicagohvz.org" % defaultfilters.slugify(self.name)

	@property
	def zombies_listhost_address(self):
		return "%s-zombies@lists.uchicagohvz.org" % defaultfilters.slugify(self.name)
		

	@models.permalink
	def get_absolute_url(self):
		return ('game|show', [self.pk])

OLD_DORMS = (
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

DORMS = (
	("BJ", "Burton-Judson Courts"),
	("IH", "International House"),
	("MAX", "Max Palevsky"),
	("NC", "North Campus"),
	("SH", "Snell-Hitchcock"),
	("SC", "South Campus"),
	("ST", "Stony Island"),
	("OFF", "Off campus")
)

DORMS_CLOSE = datetime(2016, 6, 14)

NOUNS = open(os.path.join(settings.BASE_DIR, "game/word-lists/nouns.txt")).read().split('\n')[:-1]
ADJECTIVES = open(os.path.join(settings.BASE_DIR, "game/word-lists/adjs.txt")).read().split('\n')[:-1]

def gen_bite_code():
	return random.choice(ADJECTIVES) + ' ' + random.choice(NOUNS)

class New_Squad(models.Model):
	class Meta:
		unique_together = (('game', 'name'))

	game = models.ForeignKey(Game, related_name='new_squads')
	name = models.CharField(max_length=128)

	def __unicode__(self):
		return "%s" % (self.name)

	@models.permalink
	def get_absolute_url(self):
		return ('new_squad|show', [self.pk])

	def get_active_players(self):
		return self.players.filter(active=True)

	def get_kills(self):
		return Kill.objects.exclude(parent=None).filter(killer__in=self.get_active_players())

	@property
	def size(self):
		return self.get_active_players().count()

	@property
	def num_humans(self):
		return self.get_active_players().filter(human=True).count()

	@property
	def num_zombies(self):
		return self.get_active_players().filter(human=False).count()

class Squad(models.Model):
	class Meta:
		unique_together = (('game', 'name'))

	game = models.ForeignKey(Game, related_name='squads')
	name = models.CharField(max_length=128)

	def __unicode__(self):
		return "%s (%s)" % (self.name, self.game)

	@models.permalink
	def get_absolute_url(self):
		return ('squad|show', [self.pk])

	def get_active_players(self):
		return self.players.filter(active=True)

	def get_kills(self):
		return Kill.objects.exclude(parent=None).filter(killer__in=self.get_active_players())

	def get_awards(self): # returns a list of awards (with duplicates if won more than once)
		awards = []
		sp = self.get_active_players()
		for aw in Award.objects.filter(players__in=self.get_active_players()).distinct():
			awpl = aw.players.filter(pk__in=sp.values_list('pk', flat=True))
			awards.append((aw, awpl))
		return awards

	@property
	def size(self):
		return self.get_active_players().count()

	@property
	def num_humans(self):
		return self.get_active_players().filter(human=True).count()

	@property
	def num_zombies(self):
		return self.get_active_players().filter(human=False).count()

	@property
	def human_points(self):
		if self.get_active_players().count() > 0:
			return 10 * sum([p.human_points for p in self.get_active_players()]) / self.get_active_players().count()
		return 0

	@property
	def zombie_points(self):
		if self.get_active_players().count() > 0:
			return 10 * sum([p.zombie_points for p in self.get_active_players()]) / self.get_active_players().count()
		return 0

	@property
	def human_rank(self):
		from data_apis import top_human_squads
		ths = top_human_squads(self.game)
		squad_score = [x['human_points'] for x in ths if x['squad_id'] == self.id][0]
		scores = [x['human_points'] for x in ths]
		return (Ranking(scores, start=1).rank(squad_score), len(ths))

	@property
	def zombie_rank(self):
		from data_apis import top_zombie_squads
		tzs = top_zombie_squads(self.game)
		squad_score = [x['zombie_points'] for x in tzs if x['squad_id'] == self.id][0]
		scores = [x['zombie_points'] for x in tzs]
		return (Ranking(scores, start=1).rank(squad_score), len(tzs))

class Player(models.Model):
	class Meta:
		unique_together = (('user', 'game'), ('game', 'bite_code'))
		ordering = ['-game__start_date', 'user__username', 'user__last_name', 'user__first_name']

	user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
	game = models.ForeignKey(Game, related_name='players')
	active = models.BooleanField(default=False)
	squad = models.ForeignKey(Squad, null=True, blank=True, related_name='players')
	new_squad = models.ForeignKey(New_Squad, null=True, blank=True, related_name='players')
	bite_code = models.CharField(max_length=255, blank=True, help_text='leave blank for automatic (re-)generation')
	dorm = models.CharField(max_length=4, choices=DORMS)
	major = models.CharField(max_length=255, blank=True, editable=settings.DEBUG, help_text='autopopulates from LDAP')
	human = models.BooleanField(default=True)
	opt_out_hvt = models.BooleanField(default=False)
	gun_requested = models.BooleanField(default=False)
	renting_gun = models.BooleanField(default=False)
	gun_returned = models.BooleanField(default=False)
	last_words = models.CharField(max_length=255, blank=True)
	lead_zombie = models.BooleanField(default=False)
	delinquent_gun = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		if self.game.status == 'registration' or not self.major: # allow updates to major during registration
			backend = UChicagoLDAPBackend()
			self.major = backend.get_user_major(self.user.username)
		if not self.bite_code:
			# (re-)generate unique bite code
			while True:
				bc = gen_bite_code()
				if not (Player.objects.filter(game=self.game, bite_code=bc).exists() or Award.objects.filter(game=self.game, code=bc).exists()):
					self.bite_code = bc
					break
		old = Player.objects.get(id=self.id) if self.id else None
		if (old and (not old.active) and self.active): # if user was newly activated
			profile = self.user.profile
			profile.subscribe_zombies_listhost = True # force subscription to zombies listhost
			profile.save()

		past_players = Player.objects.filter(user=self.user).exclude(game=self.game)

		if past_players and (not past_players[0].gun_returned) and past_players[0].renting_gun:
			self.delinquent_gun = True

		super(Player, self).save(*args, **kwargs)

	@property
	def kill_object(self):
		kills = Kill.objects.exclude(parent=None).filter(victim=self).order_by('-date')
		if kills.exists():
			return kills[0]
		return None

	@property
	def killed_by(self):
		ko = self.kill_object
		if ko:
			return ko.killer
		return None

	@property
	def time_of_death(self):
		if self.human == False and self.kill_object:
			return self.kill_object.date
		return None

	@property
	def lifespan(self):
		if self.game.status == 'in_progress':
			end_time = timezone.now()
		elif self.game.status == 'finished':
			end_time = self.game.end_date
		else:
			return None
		if not self.human:
			end_time = self.time_of_death
		return end_time - self.game.start_date

	@property
	def kills(self):
		return Kill.objects.filter(killer=self).exclude(victim__id=self.id).order_by('-date')

	@property
	def unannotated_kills(self):
		return Kill.objects.exclude(killer=self, victim=self).filter(killer=self).filter(Q(lat__isnull=True) | Q(lng__isnull=True) | Q(notes=u''))

	@transaction.atomic
	def kill_me(self, killer):
		if not self.human:
			return None
		parent_kills = Kill.objects.filter(victim=killer).order_by('-date')
		if parent_kills.exists():
			parent_kill = parent_kills[0]
		else:
			parent_kill = None
		points = 0
		now = timezone.now()
		try:
			hvt = HighValueTarget.objects.get(player=self, start_date__lte=now, end_date__gte=now)
		except HighValueTarget.DoesNotExist:
			hvt = None
		else:
			points += hvt.kill_points
		try:
			hvd = HighValueDorm.objects.get(game=self.game, dorm=self.dorm, start_date__lte=now, end_date__gte=now)
		except HighValueDorm.DoesNotExist:
			hvd = None
		else:
			points += hvd.points
		if not (hvt or hvd):
			points = settings.HUMAN_KILL_POINTS
		return Kill.objects.create(parent=parent_kill, killer=killer, victim=self, points=points, date=now, hvt=hvt, hvd=hvd)

	@property
	def display_name(self): # real name when game is over; otherwise, dorm + obfuscated code for humans and bite code for zombies
		name = ''
		if self.game.status == 'in_progress':
			if self.human:
				name = "%s %s" % (self.get_dorm_display(), hashlib.sha256(self.bite_code).hexdigest()[:2].upper())
			else:
				name = self.bite_code
		else:
			name = self.user.get_full_name()
		if not name:
			name = "CONTACT A MODERATOR"
		if self.squad:
			name = "%s [%s]" % (name, self.squad.name)
		elif self.new_squad:
			name = "%s [%s]" % (name, self.new_squad.name)
		return name

	@property
	def human_points(self):
		hvt_points = 0
		if self.human:
			try:
				hvt_points = self.hvt.award_points
			except HighValueTarget.DoesNotExist:
				hvt_points = 0
		return (self.awards.filter(redeem_type__in=('H', 'A')).aggregate(points=models.Sum('points'))['points'] or 0) + hvt_points

	@property
	def zombie_points(self):
		kill_points = Kill.objects.exclude(parent=None, killer=self, victim=self).filter(killer=self).aggregate(points=models.Sum('points'))['points'] or 0
		award_points =  self.awards.filter(redeem_type__in=('Z', 'A')).aggregate(points=models.Sum('points'))['points'] or 0
		return kill_points + award_points

	@property
	def human_rank(self):
		from data_apis import top_humans
		th = top_humans(self.game)
		try:
			player_score = [x['human_points'] for x in th if x['player_id'] == self.id][0]
		except IndexError:
			player_score = None
		scores = [x['human_points'] for x in th]
		return (Ranking(scores, start=1).rank(player_score), len(th))

	@property
	def zombie_rank(self):
		from data_apis import top_zombies
		tz = top_zombies(self.game)
		try:
			player_score = [x['zombie_points'] for x in tz if x['player_id'] == self.id][0]
		except IndexError:
			return None
		scores = [x['zombie_points'] for x in tz]
		return (Ranking(scores, start=1).rank(player_score), len(tz))

	def __unicode__(self):
		name = self.user.get_full_name()
		if self.squad:
			name = "%s [%s]" % (name, self.squad.name)
		return "%s, %s, %s, %s" % (self.user.username, name, self.bite_code, self.game.name)

	@models.permalink
	def get_absolute_url(self):
		return ('player|show', [self.pk])

class MissionPicture(models.Model):
	players = models.ManyToManyField(Player, related_name='pictures', blank=True, help_text='Players in this picture.')
	game = models.ForeignKey(Game, related_name="pictures")
	picture = models.FileField(upload_to=gen_pics_filename, storage=OverwriteFileSystemStorage())
	lat = models.FloatField(null=True, blank=True, verbose_name='latitude')
	lng = models.FloatField(null=True, blank=True, verbose_name='longitude')

	def __unicode__(self):
		name = ""
		for p in self.players.all():
			name += p.user.get_full_name() + " "
		name += self.game.name
		return name

	@property
	def geotagged(self):
	    return self.lat and self.lng

	@models.permalink
	def get_absolute_url(self):
		return ('mission_picture|show', [self.pk])
	

class Kill(MPTTModel):
	class Meta:
		ordering = ['-date']
		unique_together = ('parent', 'killer', 'victim')
	class MPTTMeta:
		order_insertion_by = ['date']

	parent = TreeForeignKey('self', null=True, blank=True, related_name='children', editable=False)
	killer = models.ForeignKey(Player, related_name="+")
	victim = models.ForeignKey(Player, related_name="+")
	date = models.DateTimeField(default=timezone.now)
	points = models.IntegerField(default=settings.HUMAN_KILL_POINTS)
	hvd = models.ForeignKey('game.HighValueDorm', verbose_name='High-value Dorm', null=True, blank=True, related_name='kills', on_delete=models.SET_NULL)
	hvt = models.OneToOneField('game.HighValueTarget', verbose_name='High-value target', null=True, blank=True, related_name='kill', on_delete=models.SET_NULL)
	notes = models.TextField(blank=True)
	lat = models.FloatField(null=True, blank=True, verbose_name='latitude')
	lng = models.FloatField(null=True, blank=True, verbose_name='longitude')

	def __unicode__(self):
		return "%s (%s) --> %s (%s) [%s]" % (self.killer.user.get_full_name(), self.killer.user.username, self.victim.user.get_full_name(), self.victim.user.username, self.killer.game.name)

	@property
	def geotagged(self):
		return self.lat and self.lng
	
	@models.permalink
	def get_absolute_url(self):
		return ('kill|show', [self.pk])

	def refresh_points(self):
		"""
		Update the number of points the kill is worth, taking into account HVT and HVD
		"""
		points = 0
		if self.hvt:
			points += self.hvt.kill_points
		if self.hvd:
			points += self.hvd.points
		if not (self.hvd or self.hvt):
			points = settings.HUMAN_KILL_POINTS
		self.points = points

	def save(self, *args, **kwargs):
		if self.killer.game != self.victim.game:
			raise Exception('killer.game and victim.game do not match.')
		try:
			parent = Kill.objects.exclude(id=self.id).filter(victim=self.killer)[0]
		except:
			parent = None
		self.parent = parent
		victim = self.victim
		victim.human = False
		victim.save()
		self.refresh_points()
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
	points = models.FloatField(help_text='Can be negative, e.g. to penalize players')
	players = models.ManyToManyField(Player, related_name='awards', blank=True, help_text='Players that should receive this award.')
	code = models.CharField(max_length=255, blank=True, help_text='leave blank for automatic (re-)generation')
	redeem_limit = models.IntegerField(
		help_text='Maximum number of players that can redeem award via code entry (set to 0 for awards to be added by moderators only)'
	)
	redeem_type = models.CharField(max_length=1, choices=REDEEM_TYPES)

	def __unicode__(self):
		return "%s (%s)" % (self.name, self.game.name)

	def save(self, *args, **kwargs):
		if not self.code:
			while True:
				code = gen_bite_code()
				if not (Award.objects.filter(game=self.game, code=code).exists() or Player.objects.filter(game=self.game, bite_code=code).exists()):
					self.code = code
					break
		super(Award, self).save(*args, **kwargs)

class HighValueTarget(models.Model):
	player = models.OneToOneField(Player, unique=True, related_name='hvt')
	start_date = models.DateTimeField()
	end_date = models.DateTimeField()
	kill_points = models.IntegerField(default=settings.HVT_KILL_POINTS, help_text='# of points zombies receive for killing this HVT')
	award_points = models.IntegerField(default=settings.HVT_AWARD_POINTS, help_text='# of points the HVT earns if he/she survives for the entire duration')

	def __unicode__(self):
		return "%s" % (self.player)
	
	def expired(self):
		return timezone.now() > self.end_date

	def save(self, *args, **kwargs):
		super(HighValueTarget, self).save(*args, **kwargs)
		try:
			kill = self.kill
		except Kill.DoesNotExist:
			return
		else:
			kill.refresh_points()
			kill.save()

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

	def save(self, *args, **kwargs):
		super(HighValueDorm, self).save(*args, **kwargs)
		from uchicagohvz.game.tasks import refresh_kill_points
		refresh_kill_points.delay(self.game.id)

class Mission(models.Model):
    class Meta:
        unique_together = ('game', 'name')
    game = models.ForeignKey(Game, related_name='missions')
    name = models.CharField(max_length=63)
    awards = models.ManyToManyField(Award, related_name='missions', blank=True, help_text='Awards associated with this mission.')
    description = models.CharField(max_length=255)
    summary = models.TextField(max_length=6000, default="")
    zombies_win = models.BooleanField(default=False) #because mods hate zombies :P


    def __unicode__(self):
        return "%s (%s)" % (self.name, self.game.name)

    def save(self, *args, **kwargs):
        super(Mission, self).save(*args, **kwargs)

    def mission_attendance(self, *args, **kwargs):
        attendees = []
        for award in self.awards.all():
            for player in award.players.all():
                if player not in attendees:
                    attendees.append(player)

        return len(attendees)

from django.db import models
import django.dispatch
from django.dispatch import receiver
from django.core.cache import cache
from uchicagohvz.game.models import *
from uchicagohvz.game.tasks import *

@receiver(models.signals.post_delete, sender=Kill, dispatch_uid='unzombify')
def unzombify(sender, **kwargs):
	victim = kwargs['instance'].victim
	if not Kill.objects.filter(victim=victim).exists():
		# don't unzombify if Kills with this victim still exist
		victim.human = True
		victim.save()

score_update_required = django.dispatch.Signal(providing_args=['game'])

@receiver(score_update_required)
def refresh_stats(sender, **kwargs):
	"""
	needs to be called whenever leaderboards (can) change:
		Add/edit/delete Kill
		Add/edit/delete Squad / edit Player's Squad
		Add/edit/delete Award
		Add/edit/delete HVT, HVD
	"""
	regenerate_stats.delay(kwargs['game'].pk)

def kill_changed(sender, **kwargs):
	score_update_required.send(sender=sender, game=kwargs['instance'].killer.game)

models.signals.post_save.connect(kill_changed, sender=Kill, dispatch_uid='kill_save')
models.signals.post_delete.connect(kill_changed, sender=Kill, dispatch_uid='kill_deleted')

def player_changed(sender, **kwargs):
	new_player = kwargs['instance']
	try:
		old_player = Player.objects.get(pk=new_player.pk)
	except sender.DoesNotExist:
		score_update_required.send(sender=sender, game=new_player.game)
		if new_player.game.status == 'in_progress' and new_player.active:
			new_player.user.profile.subscribe_zombies_listhost = True
			new_player.user.profile.save()
	else:
		if old_player.squad != new_player.squad or old_player.active != new_player.active:
			score_update_required.send(sender=sender, game=new_player.game)
		if old_player.human != new_player.human:
			update_chat_privs.delay(new_player.pk)
	if new_player.active and new_player.game.status in ('registration', 'in_progress'):
		new_player.user.profile.subscribe_zombies_listhost = True
		new_player.user.profile.save()

def player_deleted(sender, **kwargs):
	score_update_required.send(sender=sender, game=kwargs['instance'].game)

models.signals.pre_save.connect(player_changed, sender=Player, dispatch_uid='player_save') 
models.signals.post_delete.connect(player_deleted, sender=Player, dispatch_uid='player_deleted')

def award_changed(sender, **kwargs):
	score_update_required.send(sender=sender, game=kwargs['instance'].game)

models.signals.post_save.connect(award_changed, sender=Award, dispatch_uid='award_saved')
models.signals.m2m_changed.connect(award_changed, sender=Award.players.through, dispatch_uid='award_m2m_changed')
models.signals.post_delete.connect(award_changed, sender=Award, dispatch_uid='award_deleted')

def hvd_changed(sender, **kwargs):
	score_update_required.send(sender=sender, game=kwargs['instance'].game)	

models.signals.post_save.connect(hvd_changed, sender=HighValueDorm, dispatch_uid='hvd_saved')

def hvd_deleted(sender, **kwargs):
	refresh_kill_points.delay(game=kwargs['instance'].game.pk)

models.signals.post_delete.connect(hvd_deleted, sender=HighValueDorm, dispatch_uid='hvd_deleted')

def hvt_changed(sender, **kwargs):
	score_update_required.send(sender=sender, game=kwargs['instance'].player.game)

models.signals.post_save.connect(hvt_changed, sender=HighValueTarget, dispatch_uid='hvt_saved')

def hvt_deleted(sender, **kwargs):
	refresh_kill_points.delay(game=kwargs['instance'].player.game.pk)

models.signals.post_delete.connect(hvt_deleted, sender=HighValueTarget, dispatch_uid='hvt_deleted')

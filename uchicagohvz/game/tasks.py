from celery import task
from django.core import mail
from uchicagohvz.game.models import Game, Kill, Award
from uchicagohvz.users.phone import CARRIERS
from uchicagohvz.game.data_apis import *
import random

@task
def regenerate_stats(game_id):
	game = Game.objects.get(pk=game_id)
	keys = ('survival_by_dorm', 'top_humans', 'top_zombies', 
		'most_courageous_dorms', 'most_infectious_dorms', 'humans_per_hour', 
		'kills_by_tod', 'humans_by_major', 'zombies_by_major'
	)
	g = globals()
	# regenerate 
	for fn in keys:
		g[fn](game, use_cache=False)

@task
def refresh_kill_points(game_id):
	"""
	Refresh the points field on Kill model
	Needs to be called when an HVT or HVD model is changed or deleted
	"""
	kills = Kill.objects.filter(killer__game__pk=game_id)
	for kill in kills:
		kill.refresh_points()
		kill.save()
	regenerate_stats(game_id)

@task
def send_death_notification(kill):
	killer = kill.killer
	victim = kill.victim
	victim_dorm_name = victim.get_dorm_display()
	game = kill.killer.game
	players_in_dorm = game.get_players_in_dorm(victim.dorm)
	players = game.players.filter(active=True, user__profile__phone_number__isnull=False, user__profile__subscribe_death_notifications=True)
	to_addrs = []
	for player in players:
		pn = player.user.profile.phone_number.replace('-', '')
		to_addrs.append(CARRIERS[player.user.profile.phone_carrier] % (pn))
	random.shuffle(to_addrs)
	body = "A human from %s was killed. %s/%s humans there are still alive."
	body = body % (victim_dorm_name, players_in_dorm.filter(human=True).count(), players_in_dorm.count())
	def gen_emails():
		MAX_RECIPIENTS = 999
		for i in range(0, len(to_addrs), MAX_RECIPIENTS):
			recipients = to_addrs[i:i + MAX_RECIPIENTS]
			email = mail.EmailMessage(body=body, to=recipients)
			yield email		
	conn = mail.get_connection()
	conn.send_messages(tuple(gen_emails()))

@task
def send_sms_confirmation(player, obj): # obj is either a kill or an award object
	if isinstance(obj, Kill):
		kill_text = "%s (%s)" % (obj.victim.user.get_full_name(), obj.victim.bite_code)
		if obj.notes:
			kill_text += " [%s]" % (obj.notes)
		body = "Kill: %s confirmed. Points earned: %s" % (kill_text, obj.points)		
	elif isinstance(obj, Award):
		body = "Code '%s' redeemed. Name: %s. Points: %s" % (obj.code, obj.name, obj.points)
	else:
		return
	phone_number = player.user.profile.phone_number.replace('-', '')
	to_addr = CARRIERS[player.user.profile.phone_carrier] % (phone_number)
	email = mail.EmailMessage(body=body, to=[to_addr])
	email.send()

@task
def send_sms_invalid_code(profile, code):
	body = "Invalid code: %s" % (code)
	phone_number = profile.phone_number.replace('-', '')
	to_addr = CARRIERS[profile.phone_carrier] % (phone_number)
	email = mail.EmailMessage(body=body, to=[to_addr])
	email.send()

#@task
#def send_sms_unregistered(player):
#	body = 'Unrecognized phone #. Add your phone # and carrier to your profile.'
#	phone_number = player.user.profile.phone_number.replace('-', '')
#    to_addr = CARRIERS[player.user.profile.phone_carrier] % (phone_number)
#    email = mail.EmailMessage(body=body, to=[to_addr])
#    email.send()


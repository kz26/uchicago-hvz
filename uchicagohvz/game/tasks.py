from celery import task
from django.core import mail
from django.db import transaction
from django.conf import settings
from uchicagohvz.game.models import Game, Player, Kill, Award
from uchicagohvz.game.forms import *
from uchicagohvz.users.models import Profile
from uchicagohvz.users.phone import CARRIERS
from uchicagohvz.game.data_apis import *
import random
import json
import re
import requests

@task(rate_limit=0.1)
def regenerate_stats(game_id):
	game = Game.objects.get(pk=game_id)
	keys = (
		'kills_per_hour',
		'survival_by_dorm',
		'top_humans',
		'top_zombies', 
		'top_human_squads',
		'top_zombie_squads',
		'most_courageous_dorms',
		'most_infectious_dorms',
		'humans_per_hour',
		'kills_by_tod',
		'humans_by_major',
		'zombies_by_major'
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
def update_chat_privs(player_id):
	player = Player.objects.get(active=True, pk=player_id)
	rooms = []
	if player.human:
		rooms.append("%s-human" % (player.game.pk))
	else:
		rooms.append("%s-zombie" % (player.game.pk))
	requests.post(settings.CHAT_ADMIN_URL + 'updateUserRooms', headers={'Content-type': 'application/json'},
		data=json.dumps({'uid': player.user.pk, 'rooms': rooms})
	)
	
@task
def process_sms_code(msisdn, text):
	code = text.lower().strip()
	code = re.sub(' {2,}', ' ', code)
	phone_number = "%s-%s-%s" % (msisdn[1:4], msisdn[4:7], msisdn[7:11])
	try:
		profile = Profile.objects.get(phone_number=phone_number)
	except:
		return
	for game in Game.objects.games_in_progress().order_by('-start_date'):
		try:
			player = Player.objects.get(game=game, user=profile.user)
		except Player.DoesNotExist:
			return
		form = BiteCodeForm(data={'bite_code': code}, killer=player)
		# player is the killer
		if form.is_valid():
			with transaction.atomic():
				kill = form.victim.kill_me(player)
				if kill:
					kill.save()
			send_sms_confirmation(player, kill)
			send_death_notification(kill)
			return
		form = AwardCodeForm(data={'code': code}, player=player)
		if form.is_valid():
			with transaction.atomic():
				award = form.award
				award.players.add(player)
				award.save()
			send_sms_confirmation(player, award)
			return
	# player has a valid number but entered an invalid code
	if code:
		send_sms_invalid_code(profile, code)

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
		body = "Kill: %s confirmed. Points: %s" % (obj.victim.bite_code, obj.points)		
	elif isinstance(obj, Award):
		body = "Mission code: %s redeemed. Name: %s, Points: %s" % (obj.code, obj.name, obj.points)
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


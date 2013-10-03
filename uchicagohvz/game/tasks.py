from celery import task
from django.core import mail
from uchicagohvz.game.models import Kill, Award
from uchicagohvz.users.phone import CARRIERS
import random

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
	body = "A human from %s was killed. %s/%s humans here are still alive."
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
		body = "Code redeemed. Name: %s. Points: %s" % (award.name, award.points)
	else:
		return
	phone_number = player.user.profile.phone_number.replace('-', '')
	to_addr = CARRIERS[player.user.profile.phone_carrier] % (phone_number)
	email = mail.EmailMessage(body=body, to=[to_addr])
	email.send()


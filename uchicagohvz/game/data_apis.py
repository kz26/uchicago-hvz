from __future__ import division
from django.shortcuts import *
from django.utils import timezone
from django.conf import settings
from cache_utils import cache_func
from datetime import timedelta
from collections import OrderedDict
from uchicagohvz.game.models import *

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def kills_per_hour(game, **kwargs):
	kills = Kill.objects.exclude(parent=None).filter(victim__game=game)
	delta = min(timezone.now(), game.end_date) - game.start_date
	hours = (delta.days * 24 * 3600 + delta.seconds) / 3600
	return kills.count() / hours

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def kills_by_tod(game, **kwargs):
	"""
	Calculate kills by time of day
	returns a 24-element (hour) array where each value is number of kills in that hour
	"""
	data = [0] * 24
	kill_dts = Kill.objects.exclude(parent=None).filter(victim__game=game).values_list('date', flat=True)
	for dt in kill_dts:
		dt = timezone.localtime(dt)
		data[dt.hour] += 1
	return data

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def kills_in_last_hour(game, **kwargs):
	delta = timezone.now() - timedelta(hours=1)
	kills = Kill.objects.exclude(parent=None).filter(victim__game=game, date__gte=delta)
	return kills.count()

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def survival_by_dorm(game, **kwargs):
	data = []
	for dorm, dormName in DORMS:
		players = game.get_players_in_dorm(dorm)
		if players.count():
			e = {'dorm': dormName, 'alive': players.filter(human=True).count(), 'original': players.count()}
			e['percent']  = 100 * e['alive'] / e['original']
			data.append(e)
	data.sort(key=lambda x: x['percent'], reverse=True)
	return data

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def top_human_squads(game, **kwargs):
	squads = Squad.objects.filter(game=game)
	data = []
	for squad in squads:
		d = {
			'squad_id': squad.id,
			'url': squad.get_absolute_url(),
			'name': squad.name,
			'size': squad.players.filter(active=True).count(),
			'num_humans': squad.players.filter(active=True, human=True).count(),
			'human_points': round(squad.human_points, 1)
		}
		data.append(d)
	data.sort(key=lambda x: x['human_points'], reverse=True)
	return data

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def top_zombie_squads(game, **kwargs):
	squads = Squad.objects.filter(game=game)
	data = []
	for squad in squads:
		if squad.players.filter(active=True, human=False).count() >= 2:
			d = {
				'squad_id': squad.id,
				'url': squad.get_absolute_url(),
				'name': squad.name,
				'size': squad.players.filter(active=True).count(),
				'num_zombies': squad.players.filter(active=True, human=False).count(),
				'kills': Kill.objects.filter(killer__in=squad.players.filter(active=True)).count(),
				'zombie_points': round(squad.zombie_points, 1)
			}
			data.append(d)
	data.sort(key=lambda x: x['zombie_points'], reverse=True)
	return data

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def top_humans(game, **kwargs):
	players = Player.objects.filter(active=True, game=game)
	data = []
	for player in players:
		d = {
			'player_id': player.id,
			'url': player.get_absolute_url(),
			'display_name': player.display_name,
			'human_points': player.human_points,
			'human': player.human
		}
		data.append(d)
	data.sort(key=lambda x: x['human_points'], reverse=True)
	return data

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def top_zombies(game, **kwargs):
	players = Player.objects.filter(active=True, game=game, human=False)
	data = []
	for player in players:
		d = {
			'player_id': player.id,
			'url': player.get_absolute_url(),
			'display_name': player.display_name,
			'kills': player.kills.count(),
			'zombie_points': player.zombie_points
		}
		data.append(d)
	data.sort(key=lambda x: x['zombie_points'], reverse=True)
	return data

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def most_courageous_dorms(game, **kwargs): # points = 100 * average human points per player in dorm
	data = []
	for dorm, dormName in DORMS:
		players = Player.objects.filter(active=True, dorm=dorm, game=game)
		pc = players.count()
		if pc != 0:
			points = 100 * (1.0 / pc) * sum([p.human_points for p in players])
		else:
			points = 0
		data.append({'dorm': dormName, 'points': points})
	data.sort(key=lambda x: x['dorm'])
	data.sort(key=lambda x: x['points'], reverse=True)
	return data

def most_infectious_dorms(game, **kwargs): # points = 100 * average zombie points per player in dorm
	data = []
	for dorm, dormName in DORMS:
		players = Player.objects.filter(active=True, dorm=dorm, game=game)
		pc = players.count()
		if pc != 0:
			points = 100 * (1.0 / pc) * sum([p.zombie_points for p in players])
		else:
			points = 0
		data.append({'dorm': dormName, 'points': points})
	data.sort(key=lambda x: x['dorm'])
	data.sort(key=lambda x: x['points'], reverse=True)
	return data

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def humans_per_hour(game, **kwargs):
	data = []
	end_date = min(timezone.now(), game.end_date)
	end_td = end_date - game.start_date
	end_hour = end_td.days * 24 + round(end_td.seconds / 3600, 0)
	for dorm, dormName in DORMS:
		sh = game.get_active_players().filter(dorm=dorm).count() # starting humans in this dorm
		d = OrderedDict([(0, sh)])
		kills = Kill.objects.exclude(parent=None).filter(victim__game=game, victim__dorm=dorm).order_by('date')
		for index, kill in enumerate(kills, 1):
			kd = max(kill.date, game.start_date) - game.start_date
			hours = kd.days * 24 + round(kd.seconds / 3600, 1)
			d[min(hours, end_hour)] = sh - index # overwrite
		if end_hour not in d:
			d[end_hour] = d[d.keys()[-1]]
		data.append({'name': dormName, 'data': d.items()})
	# add dataset for all dorms
	sh = game.get_active_players().count() - Kill.objects.filter(parent=None, killer__game=game).count() # subtract LZs
	d = OrderedDict([(0, sh)])
	kills = Kill.objects.exclude(parent=None).filter(victim__game=game).order_by('date')
	for index, kill in enumerate(kills, 1):
		kd = max(kill.date, game.start_date) - game.start_date
		hours = kd.days * 24 + round(kd.seconds / 3600, 1)
		d[min(hours, end_hour)] = sh - index # overwrite
	if end_hour not in d:
		d[end_hour] = d[d.keys()[-1]]
	data.append({'name': 'ALL', 'data': d.items()})
	return data

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def humans_by_major(game, **kwargs):
	data = []
	players = game.players.filter(active=True)
	majors = players.order_by('major').values_list('major', flat=True).distinct()
	max_lifespan = min(game.end_date, timezone.now()) - game.start_date
	max_lifespan_hours = max_lifespan.days * 24 + round(max_lifespan.seconds / 3600, 0)
	
	for major in majors:
		point = {}
		kills = Kill.objects.exclude(parent=None).filter(victim__game=game, victim__major=major).order_by('date')
		kill_victim_ids = kills.values_list('victim__id', flat=True)
		live_players = Player.objects.exclude(id__in=kill_victim_ids).filter(active=True, game=game, major=major, human=True)
		lifespans = []
		for kill in kills:
			lifespans.append(kill.date - game.start_date)
		for _ in range(live_players.count()):
			lifespans.append(max_lifespan)
		if lifespans:
			total_ls = sum(lifespans, timedelta())
			avg_ls_seconds = (total_ls.days * 24 * 3600 + total_ls.seconds) / len(lifespans)
			avg_ls_hours = round(avg_ls_seconds / 3600, 1)
		else:
			avg_ls_hours = max_lifespan_hours
		point['x'] = avg_ls_hours
		major_players = players.filter(major=major)
		if major_players.count():
			major_avg_pts = round(sum([p.human_points for p in major_players]) / major_players.count(), 2)
		else:
			major_avg_pts = 0
		point['y'] = major_avg_pts
		point['name'] = major_players.count()
		
		data.append({
			'name': major,
			'data': [point]
		})
	return data

@cache_func(settings.LEADERBOARD_CACHE_DURATION)
def zombies_by_major(game, **kwargs):
	data = []
	players = game.players.filter(active=True, human=False)
	end_date = min(timezone.now(), game.end_date)
	majors = players.order_by('major').values_list('major', flat=True).distinct()
	for major in majors:
		point = {}
		kills = Kill.objects.filter(victim__game=game, victim__major=major).order_by('date')
		tszs = [] # list of time spent as zombie
		for kill in kills:
			tszs.append(end_date - kill.date)
		if tszs:
			total_tsz = sum(tszs, timedelta())
			avg_tsz_seconds = (total_tsz.days * 24 * 3600 + total_tsz.seconds) / len(tszs)
			avg_tsz_hours = round(avg_tsz_seconds / 3600, 1)
		else:
			avg_tsz_hours = 0
		point['x'] = avg_tsz_hours
		major_players = players.filter(major=major)
		if major_players.count():
			major_avg_pts = round(sum([p.zombie_points for p in major_players]) / major_players.count(), 2)
		else:
			major_avg_pts = 0
		point['y'] = major_avg_pts
		point['name'] = major_players.count()

		data.append({
			'name': major,
			'data': [point]
		})
	return data


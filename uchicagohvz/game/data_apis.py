from django.db import models
from django.shortcuts import *
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.dispatch import receiver
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import serializers
from uchicagohvz.game.models import *
from datetime import timedelta
from collections import OrderedDict

@receiver(models.signals.post_save, sender=Player)
def invalidate_cached_data(sender, **kwargs):
	update_fields = kwargs['update_fields']
	if update_fields and 'points' in update_fields:
		game = kwargs['instance'].game
		keys = ('survival_by_dorm', 'top_humans', 'top_zombies', 
			'most_courageous_dorms', 'most_infectious_dorms', 'humans_per_hour', 
			'kills_by_tod', 'humans_by_major', 'zombies_by_major'
		)
		keys = ["%s_%s" % (k, game.id) for k in keys]
		cache.delete_many(keys)

def kills_per_hour(game):
	kills = Kill.objects.filter(victim__game=game)
	delta = min(timezone.now(), game.end_date) - game.start_date
	hours = delta.days * 24 + float(delta.seconds) / 3600
	return float(kills.count()) / hours

def survival_by_dorm(game):
	key = "%s_%s" % ('survival_by_dorm', game.id)
	data = cache.get(key)
	if settings.DEBUG or data is None:
		data = []
		for dorm, dormName in DORMS:
			players = game.get_players_in_dorm(dorm)
			if players.count():
				e = {'dorm': dormName, 'alive': players.filter(human=True).count(), 'original': players.count()}
				e['percent']  = 100 * float(e['alive']) / e['original']
				data.append(e)
		data.sort(key=lambda x: x['percent'], reverse=True)
		cache.set(key, data, settings.LEADERBOARD_CACHE_DURATION)
	return data

def top_humans(game):
	key = "%s_%s" % ('top_humans', game.id)
	data = cache.get(key)
	if settings.DEBUG or data is None:
		players = Player.objects.filter(active=True, game=game)
		data = []
		for player in players:
			d = {
				'display_name': player.display_name,
				'human_points': player.human_points
			}
			data.append(d)
		data.sort(key=lambda x: x['human_points'], reverse=True)
		cache.set(key, data, settings.LEADERBOARD_CACHE_DURATION)
	return data

def top_zombies(game):
	key = "%s_%s" % ('top_zombies', game.id)
	data = cache.get(key)
	if settings.DEBUG or data is None:
		players = Player.objects.filter(active=True, game=game)
		data = []
		for player in players:
			d = {
				'display_name': player.display_name,
				'kills': player.kills.count(),
				'zombie_points': player.zombie_points
			}
			data.append(d)
		data.sort(key=lambda x: x['zombie_points'], reverse=True)
		cache.set(key, data, settings.LEADERBOARD_CACHE_DURATION)
	return data

def most_courageous_dorms(game): # defined as (1 / humans in dorm) * dorm's current human points
	key = "%s_%s" % ('most_courageous_dorms', game.id)
	data = cache.get(key)
	if settings.DEBUG or data is None:
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
		cache.set(key, data, settings.LEADERBOARD_CACHE_DURATION)
	return data

def most_infectious_dorms(game): # defined as (1 / zombies in dorm) * total zombie points
	key = "%s_%s" % ('most_infectious_dorms', game.id)
	data = cache.get(key)
	if settings.DEBUG or data is None:
		data = []
		for dorm, dormName in DORMS:
			players = Player.objects.filter(active=True, dorm=dorm, game=game, human=False)
			pc = players.count()
			if pc != 0:
				points = 100 * (1.0 / pc) * sum([p.zombie_points for p in players])
			else:
				points = 0
			data.append({'dorm': dormName, 'points': points})
		data.sort(key=lambda x: x['dorm'])
		data.sort(key=lambda x: x['points'], reverse=True)
		cache.set(key, data, settings.LEADERBOARD_CACHE_DURATION)
	return data

class KillSerializer(serializers.ModelSerializer):
	class Meta:
		model = Kill
		fields = ('killer', 'victim', 'location', 'date', 'points', 'notes')

	killer = serializers.SerializerMethodField('get_killer')
	victim = serializers.SerializerMethodField('get_victim')
	location = serializers.SerializerMethodField('get_location')

	def get_killer(self, obj):
		return obj.killer.display_name

	def get_victim(self, obj):
		return obj.victim.display_name

	def get_location(self, obj):
		if not (obj.lat and obj.lng):
			return None
		return (obj.lat, obj.lng)


class KillFeed(ListAPIView):
	serializer_class = KillSerializer

	def get_queryset(self):
		game = get_object_or_404(Game, id=self.kwargs['pk'])
		return Kill.objects.exclude(parent=None).filter(victim__game=game).order_by('-date')

class HumansPerHour(APIView):
	def get(self, request, *args, **kwargs):
		game = get_object_or_404(Game, id=kwargs['pk'])
		key = "%s_%s" % ('humans_per_hour', game.id)
		data = cache.get(key)
		if settings.DEBUG or data is None:
			data = []
			end_date = min(timezone.now(), game.end_date)
			end_td = end_date - game.start_date
			end_hour = end_td.days * 24 + round(float(end_td.seconds) / 3600, 0)
			for dorm, dormName in DORMS:
				sh = game.get_active_players().filter(dorm=dorm).count() # starting humans in this dorm
				d = OrderedDict([(0, sh)])
				kills = Kill.objects.filter(victim__game=game, victim__dorm=dorm).order_by('date')
				for index, kill in enumerate(kills, 1):
					kd = kill.date - game.start_date
					hours = kd.days * 24 + round(float(kd.seconds) / 3600, 0)
					d[hours] = sh - index # overwrite
				d[end_hour] = Player.objects.filter(game=game, active=True, dorm=dorm, human=True).count()
				data.append({'name': dormName, 'data': d.items()})
			# add dataset for all dorms
			sh = game.get_active_players().count() - Kill.objects.filter(parent=None, killer__game=game).count() # subtract LZs
			d = OrderedDict([(0, sh)])
			kills = Kill.objects.exclude(parent=None).filter(victim__game=game).order_by('date')
			for index, kill in enumerate(kills, 1):
				kd = kill.date - game.start_date
				hours = kd.days * 24 + round(float(kd.seconds) / 3600, 0)
				d[hours] = sh - index # overwrite
			d[end_hour] = Player.objects.filter(game=game, active=True, human=True).count()
			data.append({'name': 'ALL', 'data': d.items()})
			cache.set(key, data, settings.LEADERBOARD_CACHE_DURATION)
		return Response(data)

class KillsByTimeOfDay(APIView):
	def get(self, request, *args, **kwargs):
		game = get_object_or_404(Game, id=kwargs['pk'])
		key = "%s_%s" % ('kills_by_tod', game.id)
		data = cache.get(key)
		if settings.DEBUG or data is None:
			data = [0] * 24
			kill_dts = Kill.objects.filter(victim__game=game).values_list('date', flat=True)
			for dt in kill_dts:
				dt = timezone.localtime(dt)
				data[dt.hour] += 1
			cache.set(key, data, settings.LEADERBOARD_CACHE_DURATION)
		return Response(data)

class HumansByMajor(APIView):
	def get(self, request, *args, **kwargs):
		game = get_object_or_404(Game, id=kwargs['pk'])
		key = "%s_%s" % ('humans_by_major', game.id)
		data = cache.get(key)
		if settings.DEBUG or data is None:
			data = []
			players = game.players.all()
			majors = players.order_by('major').values_list('major', flat=True).distinct()
			max_lifespan = min(game.end_date, timezone.now()) - game.start_date
			max_lifespan_hours = max_lifespan.days * 24 + round(float(max_lifespan.seconds) / 3600, 0)
			
			for major in majors:
				point = {}
				kills = Kill.objects.exclude(parent=None).filter(victim__game=game, victim__major=major).order_by('date')
				lifespans = []
				for kill in kills:
					lifespans.append(kill.date - game.start_date)
				if lifespans:
					avg_ls = sum(lifespans, timedelta()) / len(lifespans)
					avg_ls_hours = avg_ls.days * 24 + round(float(avg_ls.seconds) / 3600, 0)
				else:
					avg_ls_hours = max_lifespan_hours
				point['x'] = avg_ls_hours
				major_players = players.filter(major=major)
				if major_players.count():
					major_avg_pts = round(float(sum([p.human_points for p in major_players])) / major_players.count(), 1)
				else:
					major_avg_pts = 0
				point['y'] = major_avg_pts
				data.append({
					'name': major if major else 'N/A',
					'data': [point]
				})
			cache.set(key,data, settings.LEADERBOARD_CACHE_DURATION)
		return Response(data)

class ZombiesByMajor(APIView):
	def get(self, request, *args, **kwargs):
		game = get_object_or_404(Game, id=kwargs['pk'])
		key = "%s_%s" % ('zombies_by_major', game.id)
		data = cache.get(key)
		if settings.DEBUG or data is None:
			data = []
			players = game.players.filter(human=False)
			end_date = min(timezone.now(), game.end_date)
			majors = players.order_by('major').values_list('major', flat=True).distinct()
			for major in majors:
				point = {}
				kills = Kill.objects.exclude(parent=None).filter(victim__game=game, victim__major=major).order_by('date')
				tszs = [] # list of time spent as zombie
				for kill in kills:
					tszs.append(end_date - kill.date)
				if tszs:
					avg_tsz = sum(tszs, timedelta()) / len(tszs)
					avg_tsz_hours = avg_tsz.days * 24 + round(float(avg_tsz.seconds) / 3600, 0)
				else:
					avg_tsz_hours = 0
				point['x'] = avg_tsz_hours
				major_players = players.filter(major=major)
				if major_players.count():
					major_avg_pts = round(float(sum([p.zombie_points for p in major_players])) / major_players.count(), 1)
				else:
					major_avg_pts = 0
				point['y'] = major_avg_pts
				data.append({
					'name': major if major else 'N/A',
					'data': [point]
				})
			cache.set(key,data, settings.LEADERBOARD_CACHE_DURATION)
		return Response(data)
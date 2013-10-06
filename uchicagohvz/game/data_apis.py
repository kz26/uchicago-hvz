from django.db import models
from django.shortcuts import *
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import serializers
from uchicagohvz.game.models import *
from datetime import timedelta

def kills_per_hour(game):
	kills = Kill.objects.filter(victim__game=game)
	delta = min(timezone.now(), game.end_date) - game.start_date
	hours = delta.days * 24 + float(delta.seconds) / 3600
	return float(kills.count()) / hours

def top_humans(game):
	players = cache.get('top_humans')
	if settings.DEBUG or players is None:
		players = list(Player.objects.filter(active=True, game=game))
		players.sort(key=lambda x: x.human_points, reverse=True)
		cache.set('top_humans', players, settings.LEADERBOARD_CACHE_DURATION)
	return players

def top_zombies(game):
	players = cache.get('top_zombies')
	if settings.DEBUG or players is None:
		players = list(Player.objects.filter(active=True, game=game, human=False))
		players.sort(key=lambda x: x.kills.count(), reverse=True)
		players.sort(key=lambda x: x.zombie_points, reverse=True)
		cache.set('top_zombies', players, settings.LEADERBOARD_CACHE_DURATION)
	return players

def most_courageous_dorms(game): # defined as (1 / humans in dorm) * dorm's current human points
	data = []
	for dorm, dormName in DORMS:
		players = Player.objects.filter(active=True, dorm=dorm, game=game, human=True)
		pc = players.count()
		if pc != 0:
			points = 1 / players.count() * players.aggregate(points=models.Count('points'))['points']
		else:
			points = 0
		data.append({'dorm': dormName, 'points': points})
	data.sort(key=lambda x: x['points'])
	data.sort(key=lambda x: x['dorm'])
	return data

def most_infectious_dorms(game): # defined as (1 / zombies in dorm) * total zombie points
	data = []
	for dorm, dormName in DORMS:
		players = Player.objects.filter(active=True, dorm=dorm, game=game, human=False)
		pc = players.count()
		if pc != 0:
			points = 1 / players.count() * players.aggregate(points=models.Count('points'))['points']
		else:
			points = 0
		data.append({'dorm': dormName, 'points': points})
	data.sort(key=lambda x: x['points'])
	data.sort(key=lambda x: x['dorm'])
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
		data = []
		for dorm, dormName in DORMS:
			sh = game.get_active_players().filter(dorm=dorm).count() # starting humans in this dorm
			d = [(0, sh)]
			kills = Kill.objects.filter(victim__game=game, victim__dorm=dorm).order_by('date')
			for index, kill in enumerate(kills, 1):
				kd = kill.date - game.start_date
				hours = kd.days * 24 + round(float(kd.seconds) / 3600, 0)
				d.append((hours, sh - index))
			data.append({'name': dormName, 'data': d})
		# add dataset for all dorms
		sh = game.get_active_players().count() - Kill.objects.filter(parent=None, killer__game=game).count() # subtract LZs
		d = [(0, sh)]
		kills = Kill.objects.exclude(parent=None).filter(victim__game=game).order_by('date')
		for index, kill in enumerate(kills, 1):
			kd = kill.date - game.start_date
			hours = kd.days * 24 + round(float(kd.seconds) / 3600, 0)
			d.append((hours, sh - index))
		data.append({'name': 'ALL', 'data': d})
		return Response(data)

class KillsByTimeOfDay(APIView):
	def get(self, request, *args, **kwargs):
		game = get_object_or_404(Game, id=kwargs['pk'])
		data = [0] * 24
		kill_dts = list(Kill.objects.filter(victim__game=game).values_list('date', flat=True))
		for dt in kill_dts:
			data[dt.hour] += 1
		return Response(data)
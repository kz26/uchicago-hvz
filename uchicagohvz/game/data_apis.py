from django.db import models
from django.shortcuts import *
from django.utils import timezone
from rest_framework.views import APIView
from django.utils import timezone
from rest_framework.response import Response
from uchicagohvz.game.models import *
from datetime import timedelta

def kills_per_hour(game):
		kills = Kill.objects.filter(victim__game=game)
		delta = timezone.now() - game.start_date
		hours = delta.days * 24 + float(delta.seconds) / 3600
		return float(kills.count()) / hours

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
		sh = game.get_active_players().count() - Kill.objects.filter(parent=None, killer__game=game).count()
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
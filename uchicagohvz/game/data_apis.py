from django.shortcuts import *
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from uchicagohvz.game.models import *
from datetime import timedelta

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
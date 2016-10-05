from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from uchicagohvz.game.models import *
from uchicagohvz.game.data_apis import *
from uchicagohvz.game.serializers import *

class KillFeed(ListAPIView):
	serializer_class = KillSerializer

	def get_queryset(self):
		game = get_object_or_404(Game, id=self.kwargs['pk'])
		return Kill.objects.exclude(parent=None).filter(killer__game=game).order_by('-date')

class PlayerKillFeed(ListAPIView):
	serializer_class = KillSerializer

	def get_queryset(self):
		player = get_object_or_404(Player, id=self.kwargs['pk'], active=True, human=False)
		return Kill.objects.exclude(parent=None).exclude(victim=player).filter(killer=player)

class SquadKillFeed(ListAPIView):
	serializer_class = KillSerializer
	def get_queryset(self):
		squad = get_object_or_404(Squad, id=self.kwargs['pk'])
		return squad.get_kills()

class NewSquadKillFeed(ListAPIView):
	serializer_class = KillSerializer
	def get_queryset(self):
		new_squad = get_object_or_404(New_Squad, id=self.kwargs['pk'])
		return new_squad.get_kills()

class PictureFeed(ListAPIView):
	serializer_class = PictureSerializer
	def get_queryset(self):
		game = get_object_or_404(Game, id=self.kwargs['pk'])
		return MissionPicture.objects.filter(game=game).order_by('-date')

class HumansPerHour(APIView):
	def get(self, request, *args, **kwargs):
		game = get_object_or_404(Game, id=kwargs['pk'])
		data = humans_per_hour(game)
		return Response(data)

class KillsByTimeOfDay(APIView):
	def get(self, request, *args, **kwargs):
		game = get_object_or_404(Game, id=kwargs['pk'])
		data = kills_by_tod(game)
		return Response(data)

class HumansByMajor(APIView):
	def get(self, request, *args, **kwargs):
		game = get_object_or_404(Game, id=kwargs['pk'])
		data = humans_by_major(game)
		return Response(data)

class ZombiesByMajor(APIView):
	def get(self, request, *args, **kwargs):
		game = get_object_or_404(Game, id=kwargs['pk'])
		data = zombies_by_major(game)
		return Response(data)

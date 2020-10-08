from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from uchicagohvz.game.models import *
from uchicagohvz.game.data_apis import *
from uchicagohvz.game.serializers import *
from uchicagohvz.users.models import Profile
import json

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

class RecordMinecraftKill(APIView):
	def post(self, request, *args, **kwargs):
		parsedBody = json.loads(request.body)

		killer_mc_user = get_object_or_404(MinecraftUser, player_uuid=parsedBody['killer'])
		killed_mc_user = get_object_or_404(MinecraftUser, player_uuid=parsedBody['killed'])
		current_game = Game.objects.all()[0]
		killer_player = get_object_or_404(Player, game=current_game, user=killer_mc_user.user)
		killed_player = get_object_or_404(Player, game=current_game, user=killed_mc_user.user)

		kill = killed_player.kill_me(killer_player)
		if kill:
			kill.save()
		return Response()

class RegisterMinecraftUser(APIView):
	def post(self, request, *args, **kwargs):
		parsedBody = json.loads(request.body)
		try:
			MinecraftUser.objects.get(player_uuid=parsedBody['uuid'])
			return Response() # if the user already exists we're good
		except:
			profile = get_object_or_404(Profile, minecraft_username=parsedBody['name'])
			MinecraftUser(user=profile.user, player_uuid=parsedBody['uuid']).save()
		return Response()

class UpdateMinecraftUser(APIView):
	def put(self, request, *args, **kwargs):
		user = get_object_or_404(MinecraftUser, player_uuid=kwargs['pk'])
		parsedBody = json.loads(request.body)
		user.human_score = int(parsedBody['human_score'])
		user.zombie_score = int(parsedBody['zombie_score'])
		user.save()
		return Response()   
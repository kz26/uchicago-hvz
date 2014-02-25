from django.shortcuts import *
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from uchicagohvz.game.models import *

# Create your views here.

class ChatView(TemplateView):
	template_name = 'chat/chat.html'

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(ChatView, self).dispatch(request, *args, **kwargs)

	def get_context_data(self, **kwargs):
		context = super(ChatView, self).get_context_data(**kwargs)
		context['game'] = get_object_or_404(Game.objects.games_in_progress(), pk=int(kwargs['pk']))
		context['player'] = get_object_or_404(context['game'].players, active=True, user=self.request.user)
		context['CHAT_SERVER_URL'] = settings.CHAT_SERVER_URL
		return context


class ChatAuth(APIView):
	permission_classes = (IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		game = get_object_or_404(Game.objects.games_in_progress(), pk=int(kwargs['pk']))
		player = get_object_or_404(game.players, active=True, user=self.request.user)
		rooms = []
		if player.human:
			rooms.append("%s-human" % (game.pk))
		else:
			rooms.append("%s-zombie" % (game.pk))
		return Response({
			'uid': request.user.pk,
			'name': request.user.get_full_name(),
			'rooms': rooms
		})

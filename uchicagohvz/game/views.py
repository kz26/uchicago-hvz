from django.shortcuts import render
from django.conf import settings
from django.views.generic import *
from uchicagohvz.game.models import *

# Create your views here.

class ListGames(ListView):
	model = Game
	template_name = "game/list.html"

class ShowGame(DetailView):
	template_name = "game/show.html"

	def get_context_data(self, **kwargs):
		context = super(ShowGame, self).get_context_data(**kwargs)
		if self.request.user.is_authenticated():
			in_game = Player.objects.filter(game=self.object, player=self.request.user).exists()
			if self.object.status == "registration" and not in_game:
				context['allow_registration'] = True
			elif self.object.status == "in_progress" and in_game:
				player = Player.objects.get(game=self.object, player=self.request.user)
				if player.active:
					context['code_form'] = True
					if not player.human:
						context['bc_form'] = True



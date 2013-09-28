from django.shortcuts import *
from django.conf import settings
from django.contrib import messages
from django.http import *
from django.views.generic import *
from django.views.generic.edit import BaseFormView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import *
from uchicagohvz.game.models import *
from uchicagohvz.game.forms import *

# Create your views here.

class ListGames(ListView):
	model = Game
	template_name = "game/list.html"

class ShowGame(DetailView):
	model = Game
	template_name = "game/show.html"

	def get_context_data(self, **kwargs):
		context = super(ShowGame, self).get_context_data(**kwargs)
		#if self.object.status == "finished":
		context['kill_tree'] = Kill.objects.filter(killer__game=self.object)
		if self.object.status in ('in_progress', 'finished'):
			context['humans_percent'] = int(round(100 * float(self.object.get_humans().count()) / self.object.get_active_players().count(), 0))
			context['zombies_percent'] = int(round(100 * float(self.object.get_zombies().count()) / self.object.get_active_players().count(), 0))
		if self.request.user.is_authenticated():
			in_game = Player.objects.filter(game=self.object, user=self.request.user).exists()
			if in_game:
				player = Player.objects.get(game=self.object, user=self.request.user)
				context['player'] = player
				if self.object.status in ('in_progress', 'finished') and player.active and not player.human:
						context['killed_by'] = player.killed_by
		return context

class SubmitBiteCode(BaseFormView):
	form_class = BiteCodeForm
	http_method_names = ['post']

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(SubmitBiteCode, self).dispatch(request, *args, **kwargs)

	def form_valid(self, form):
		victim = form.victim
		victim.human = False
		victim.save()
		parent_kills = Kill.objects.filter(victim=self.player).order_by('-date')
		if parent_kills.exists():
			parent_kill = parent_kills[0]
		else:
			parent_kill = None
		Kill.objects.create(parent=parent_kill, killer=self.player, victim=victim, date=timezone.now())
		messages.success(self.request, "Bite code entered successfully! %s has joined the ranks of the undead." % (victim.user.get_full_name()))
		return HttpResponseRedirect(self.game.get_absolute_url())

	def form_invalid(self, form):
		messages.error(self.request, "Invalid bite code entered.")
		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_form_kwargs(self):
		kwargs = super(SubmitBiteCode, self).get_form_kwargs()
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		self.player = get_object_or_404(Player, game=self.game, active=True, human=False, user=self.request.user)
		kwargs['player'] = self.player
		return kwargs

class RegisterForGame(FormView):
	form_class = GameRegistrationForm
	template_name = "game/register.html"

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		if not (self.game.registration_date < timezone.now() < self.game.start_date):
			return HttpResponseForbidden()
		if Player.objects.filter(game=self.game, user=request.user).exists():
			return HttpResponseForbidden()
		return super(RegisterForGame, self).dispatch(request, *args, **kwargs)

	def form_valid(self, form):
		Player.objects.create(user=self.request.user, game=self.game, dorm=form.cleaned_data['dorm'])
		messages.success(self.request, "You are now registered for %s!" % (self.game.name))
		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_context_data(self, **kwargs):
		context = super(RegisterForGame, self).get_context_data(**kwargs)
		context['game'] = self.game
		return context
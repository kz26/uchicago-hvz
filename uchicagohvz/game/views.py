from __future__ import division
from django.shortcuts import *
from django.conf import settings
from django.db import transaction
from django.contrib import messages
from django.http import *
from django.core.exceptions import *
from django.views.generic import *
from django.views.generic.edit import BaseFormView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import *
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from uchicagohvz.game.models import *
from uchicagohvz.game.forms import *
from uchicagohvz.game.data_apis import *
from uchicagohvz.game.tasks import *
from uchicagohvz.users.models import *
import re

# Create your views here.

class ListGames(ListView):
	model = Game
	template_name = 'game/list.html'

class ShowGame(DetailView):
	model = Game
	template_name = 'game/show.html'

	def get_context_data(self, **kwargs):
		context = super(ShowGame, self).get_context_data(**kwargs)
		if self.object.status in ('in_progress', 'finished'):
			if self.object.get_active_players().count() > 0:
				context['humans_percent'] = int(round(100 * self.object.get_humans().count() / self.object.get_active_players().count(), 0))
				context['zombies_percent'] = int(round(100 * self.object.get_zombies().count() / self.object.get_active_players().count(), 0))
				if self.object.status == "in_progress":
					context['sms_code_number'] = settings.NEXMO_NUMBER
				context['kills_per_hour'] = kills_per_hour(self.object)
				context['kills_in_last_hour'] = kills_in_last_hour(self.object)
				context['survival_by_dorm'] = survival_by_dorm(self.object)
				context['most_courageous_dorms'] = most_courageous_dorms(self.object)
				context['most_infectious_dorms'] = most_infectious_dorms(self.object)
				context['top_humans'] = top_humans(self.object)[:10]
				context['top_zombies'] = top_zombies(self.object)[:10]
				context['squad_count'] = self.object.squads.count()

				if self.object.squads.count():
					context['top_human_squads'] = top_human_squads(self.object)
					context['top_zombie_squads'] = top_zombie_squads(self.object)
		if self.request.user.is_authenticated():
			in_game = Player.objects.filter(game=self.object, user=self.request.user).exists()
			if in_game:
				player = Player.objects.get(game=self.object, user=self.request.user)
				context['player'] = player
				if self.object.status in ('in_progress', 'finished') and player.active:
					if player.human:
						context['player_rank'] = player.human_rank
					else:
						context['player_rank'] = player.zombie_rank
		return context


class RegisterForGame(FormView):
	form_class = GameRegistrationForm
	template_name = "game/register.html"

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		if self.game.status != 'registration' or Player.objects.filter(game=self.game, user=request.user).exists():
			return HttpResponseRedirect(self.game.get_absolute_url())
		return super(RegisterForGame, self).dispatch(request, *args, **kwargs)

	def form_valid(self, form):
		player = form.save(commit=False)
		player.user = self.request.user
		player.game = self.game
		player.save()
		messages.success(self.request, "You are now registered for %s!" % (self.game.name))
		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_context_data(self, **kwargs):
		context = super(RegisterForGame, self).get_context_data(**kwargs)
		context['game'] = self.game
		return context

class ChooseSquad(FormView):
	form_class = SquadForm
	template_name = 'game/choose_squad.html'

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		return super(ChooseSquad, self).dispatch(request, *args, **kwargs)

	def form_valid(self, form):	
		try:
			player = Player.objects.get(game=self.game, user=self.request.user)
		except:
			return HttpResponseRedirect(self.game.get_absolute_url())


		if form.squad_name:
			try:
				new_squad = New_Squad.objects.create(game=form.game, name=form.squad_name)
				player.new_squad = new_squad
			except:
				messages.error(self.request, "There is already a squad named %s. Please join %s or use a different squad name." % (form.squad_name, form.squad_name))
				return HttpResponseRedirect(self.request.get_full_path())

		elif form.squad:
			player.new_squad = form.squad

		player.save()

		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_form_kwargs(self):
		kwargs = super(ChooseSquad, self).get_form_kwargs()
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		kwargs['game'] = self.game
		return kwargs

class EnterBiteCode(FormView):
	form_class = BiteCodeForm
	template_name = 'game/enter-bite-code.html'

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(EnterBiteCode, self).dispatch(request, *args, **kwargs)

	def form_valid(self, form):
		victim = form.victim
		kill = victim.kill_me(self.killer)
		if kill:
			send_death_notification.delay(kill)
			kill.lat = form.cleaned_data.get('lat')
			kill.lng = form.cleaned_data.get('lng')
			kill.notes = form.cleaned_data.get('notes')
			kill.save()
			victim_profile = Profile.objects.get(user=victim.user)
			messages.success(self.request, mark_safe("Kill logged successfully! <b>%s</b> has joined the ranks of the undead." % (victim.user.get_full_name())))
			if victim_profile.last_words:
				victim.last_words = victim_profile.last_words
				victim.save()
				messages.error(self.request, escape("{0}'s last words: {1}".format(victim.user.get_full_name(), victim.last_words)))
		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_form_kwargs(self):
		kwargs = super(EnterBiteCode, self).get_form_kwargs()
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		if self.game.status == 'in_progress':
			self.killer = get_object_or_404(Player, game=self.game, active=True, human=False, user=self.request.user)
			kwargs['killer'] = self.killer
			kwargs['require_location'] = True
			return kwargs
		else:
			raise PermissionDenied

	def get_context_data(self, **kwargs):
		context = super(EnterBiteCode, self).get_context_data(**kwargs)
		return context

class AnnotateKill(UpdateView):
	form_class = AnnotateKillForm
	model = Kill
	template_name = 'game/annotate-kill.html'

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(AnnotateKill, self).dispatch(request, *args, **kwargs)

	def get_object(self, queryset=None):
		kill = super(AnnotateKill, self).get_object()
		if kill.killer.user == self.request.user:
			return kill
		raise PermissionDenied

	def form_valid(self, form):
		kill = form.save()
		messages.success(self.request, 'Kill annotated successfully.')
		return HttpResponseRedirect(kill.killer.game.get_absolute_url())

class SubmitCodeSMS(APIView):
	@method_decorator(csrf_exempt)
	def post(self, request, *args, **kwargs):
		if all([f in request.DATA for f in ('msisdn', 'text')]):
			process_sms_code.delay(request.DATA['msisdn'], request.DATA['text'])
		return Response()

class SubmitAwardCode(BaseFormView):
	form_class = AwardCodeForm
	http_method_names = ['post']

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(SubmitAwardCode, self).dispatch(request, *args, **kwargs)

	@transaction.atomic
	def form_valid(self, form):
		award = form.award
		award.players.add(self.player)
		award.save()
		messages.success(self.request, mark_safe("Code entry for <b>%s</b> accepted!" % (award.name)))
		return HttpResponseRedirect(self.game.get_absolute_url())

	def form_invalid(self, form):
		for e in form.non_field_errors():
			messages.error(self.request, e)
		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_form_kwargs(self):
		kwargs = super(SubmitAwardCode, self).get_form_kwargs()
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		if self.game.status == 'in_progress':
			self.player = get_object_or_404(Player, game=self.game, active=True, user=self.request.user)
			kwargs['player'] = self.player
			return kwargs
		else:
			raise PermissionDenied

class ShowPlayer(DetailView):
	model = Player
	template_name = 'game/show_player.html'

	def get_object(self, queryset=None):
		return get_object_or_404(Player, id=self.kwargs['pk'], active=True)

	def get_context_data(self, **kwargs):
		context = super(ShowPlayer, self).get_context_data(**kwargs)
		player = self.object
		if (not player.human) and (player.user == self.request.user or player.game.status == 'finished'):
			try:
				my_kill = Kill.objects.filter(victim=player)[0]
				context['kill_tree'] = my_kill.get_descendants()
			except:
				pass
		return context

class Leaderboard(DetailView):
	model = Game
	template_name = 'game/leaderboard.html'

	def get_context_data(self, **kwargs):
		context = super(Leaderboard, self).get_context_data(**kwargs)
		game = context['game']
		if game.status in ('in_progress', 'finished'):
			context['top_humans'] = top_humans(game)
			context['top_zombies'] = top_zombies(game)
			return context
		else:
			raise Http404

class ShowSquad(DetailView):
	model = Squad
	template_name = 'game/show_squad.html'

class ShowKill(DetailView):
	model = Kill
	template_name = 'game/show_kill.html'
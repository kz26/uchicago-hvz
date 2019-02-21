from __future__ import division
from django.shortcuts import *
from django.conf import settings
from django.db import transaction
from django.db.models.expressions import RawSQL
from django.contrib import messages
from django.http import *
from django.core.exceptions import *
from django.views.generic import *
from django.views.generic.edit import BaseFormView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import *
from django.utils.safestring import mark_safe
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

	def get_queryset(self):
		qs = super(ListGames, self).get_queryset()
		if self.request.user.is_authenticated():
			current_game = Game.objects.all()[0]
			past_players = Player.objects.filter(user=self.request.user).exclude(game=current_game)
			try:
				player = Player.objects.get(game=current_game, user=self.request.user)

				if past_players and (not past_players[0].gun_returned) and past_players[0].renting_gun:
					player.delinquent_gun = True
					player.save()
			except:
				pass

			qs = qs.annotate(is_player=RawSQL("SELECT EXISTS(SELECT 1 FROM game_player WHERE \
				game_player.game_id = game_game.id AND game_player.user_id = %s AND \
				game_player.active = true)", (self.request.user.id,)))	
		return qs

class ShowGame(DetailView):
	model = Game
	template_name = 'game/show.html'

	def get_context_data(self, **kwargs):

		for squad in New_Squad.objects.all():
			if squad.players.count() == 0:
				squad.delete()

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
				context['missions'] = self.object.missions.all()

				if self.object.squads.count():
					context['top_human_squads'] = top_human_squads(self.object)
					context['top_zombie_squads'] = top_zombie_squads(self.object)
		if self.request.user.is_authenticated():
			in_game = Player.objects.filter(game=self.object, user=self.request.user).exists()
			if in_game:
				player = Player.objects.get(game=self.object, user=self.request.user)
				context['player'] = player

				past_players = Player.objects.filter(user=self.request.user).exclude(game=self.object)

				if past_players and (not past_players[0].gun_returned) and past_players[0].renting_gun:
					player.delinquent_gun = True
					player.save()


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

	def get_form_kwargs(self):
		kwargs = super(RegisterForGame, self).get_form_kwargs()
		kwargs['game'] = self.game
		return kwargs

class ChooseSquad(FormView):
	form_class = SquadForm
	template_name = 'game/choose_squad.html'

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		self.player = get_object_or_404(Player, game=self.game, user=self.request.user)
		return super(ChooseSquad, self).dispatch(request, *args, **kwargs)

	def form_valid(self, form):
		if form.cleaned_data['create_squad']:
			self.player.new_squad = New_Squad.objects.create(
				game=self.game, name=form.cleaned_data['create_squad'])
		elif form.cleaned_data['choose_squad']:
			self.player.new_squad = form.cleaned_data['choose_squad']
		self.player.save(update_fields=['new_squad'])
		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_form_kwargs(self):
		kwargs = super(ChooseSquad, self).get_form_kwargs()
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
			messages.success(self.request, mark_safe(
				u"Kill logged successfully! <b>%s</b> has joined the ranks of the undead." % (victim.user.get_full_name())))
			if victim_profile.last_words:
				victim.last_words = victim_profile.last_words
				victim.save()
				messages.error(self.request, mark_safe(
					u"{0}'s last words: {1}".format(victim.user.get_full_name(), victim.last_words)))
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
		if all([f in request.data for f in ('msisdn', 'text')]):
			process_sms_code.delay(request.data['msisdn'], request.data['text'])
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

class SubmitDiscordTag(BaseFormView):
	form_class = DiscordTagForm
	http_method_names = ['post']

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(SubmitDiscordTag, self).dispatch(request, *args, **kwargs)

	@transaction.atomic
	def form_valid(self, form):
		tag = form.tag
		messages.success(self.request, mark_safe("Registered Discord Tag!"))
		return HttpResponseRedirect(self.game.get_absolute_url())

	def form_invalid(self, form):
		for e in form.non_field_errors():
			messages.error(self.request, e)
		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_form_kwargs(self):
		kwargs = super(SubmitDiscordTag, self).get_form_kwargs()
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		self.player = get_object_or_404(Player, game=self.game, active=True, user=self.request.user)
		kwargs['user'] = self.request.user
		kwargs['player'] = self.player
		return kwargs

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

class ShowNewSquad(DetailView):
	model = New_Squad
	template_name = 'game/show_new_squad.html'

class ShowKill(DetailView):
	model = Kill
	template_name = 'game/show_kill.html'

class ShowMission(DetailView):
	model = Mission
	template_name = 'game/show_mission.html'

class UploadMissionPicture(FormView):
    form_class = UploadMissionPictureForm
    model = MissionPicture
    template_name = 'game/upload-mission-picture.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(UploadMissionPicture, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        mission_picture = super(UploadMissionPicture, self).get_object()
        if mission_picture.player.user == self.request.user:
            return mission_picture
        raise PermissionDenied

    def form_valid(self, form):
        mission_picture = form.save(commit=False)
        mission_picture.game = get_object_or_404(Game, id=self.kwargs['pk'])
        mission_picture.save()
        messages.success(self.request, 'Picture successfully uploaded.')
        return HttpResponseRedirect(mission_picture.game.get_absolute_url())

    def get_form_kwargs(self):
    	kwargs = super(UploadMissionPicture, self).get_form_kwargs()
    	self.game = get_object_or_404(Game, id=self.kwargs['pk'])
    	kwargs['game'] = self.game
    	return kwargs


class SendZombieText(BaseFormView):
    form_class = ZombieTextForm
    http_method_names = ['post']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
    	self.game = get_object_or_404(Game, id=self.kwargs['pk'])
        return super(SendZombieText, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
    	if self.game.status == 'in_progress':
            self.player = get_object_or_404(Player, game=self.game, active=True, user=request.user)
            if not self.player.lead_zombie:
            	raise PermissionDenied
            return super(SendZombieText, self).post(request, *args, **kwargs)
        else:
        	raise PermissionDenied

    @transaction.atomic
    def form_valid(self, form):
        message = form.message
        send_zombie_text(message)
        messages.success(self.request, mark_safe("Message sent to subscribing zombies!"))
        return HttpResponseRedirect(self.game.get_absolute_url())

    def form_invalid(self, form):
        for e in form.non_field_errors():
            messages.error(self.request, e)
        return HttpResponseRedirect(self.game.get_absolute_url())

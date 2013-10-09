from django.shortcuts import *
from django.conf import settings
from django.db import transaction
from django.contrib import messages
from django.http import *
from django.views.generic import *
from django.views.generic.edit import BaseFormView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import *
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from uchicagohvz.game.models import *
from uchicagohvz.game.forms import *
from uchicagohvz.game.data_apis import *
from uchicagohvz.game.serializers import *
from uchicagohvz.game.tasks import *

# Create your views here.

class ListGames(ListView):
	model = Game
	template_name = "game/list.html"

class ShowGame(DetailView):
	model = Game
	template_name = "game/show.html"

	def get_context_data(self, **kwargs):
		context = super(ShowGame, self).get_context_data(**kwargs)
		if self.object.status == 'finished':
			context['kill_tree'] = Kill.objects.filter(killer__game=self.object)
		if self.object.status in ('in_progress', 'finished'):
			if self.object.get_active_players().count() > 0:
				context['humans_percent'] = int(round(100 * float(self.object.get_humans().count()) / self.object.get_active_players().count(), 0))
				context['zombies_percent'] = int(round(100 * float(self.object.get_zombies().count()) / self.object.get_active_players().count(), 0))
				if self.object.status == "in_progress":
					context['sms_code_number'] = settings.NEXMO_NUMBER
				context['kills_per_hour'] = kills_per_hour(self.object)
				context['most_courageous_dorms'] = most_courageous_dorms(self.object)
				context['most_infectious_dorms'] = most_infectious_dorms(self.object)
				context['top_humans'] = top_humans(self.object)[:10]
				context['top_zombies'] = top_zombies(self.object)[:10]
		if self.request.user.is_authenticated():
			in_game = Player.objects.filter(game=self.object, user=self.request.user).exists()
			if in_game:
				player = Player.objects.get(game=self.object, user=self.request.user)
				context['player'] = player
				if self.object.status in ('in_progress', 'finished') and player.active and not player.human:
						context['killed_by'] = player.killed_by
		return context

class RegisterForGame(FormView):
	form_class = GameRegistrationForm
	template_name = "game/register.html"

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		if self.game.status != 'registration':
			return HttpResponseForbidden()
		if Player.objects.filter(game=self.game, user=request.user).exists():
			return HttpResponseRedirect(self.game.get_absolute_url())
		return super(RegisterForGame, self).dispatch(request, *args, **kwargs)

	def form_valid(self, form):
		Player.objects.create(user=self.request.user, game=self.game, dorm=form.cleaned_data['dorm'], renting_gun=form.cleaned_data['renting_gun'])
		messages.success(self.request, "You are now registered for %s!" % (self.game.name))
		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_context_data(self, **kwargs):
		context = super(RegisterForGame, self).get_context_data(**kwargs)
		context['game'] = self.game
		return context

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
			kill.save()
			messages.success(self.request, "Bite code entered successfully! %s has joined the ranks of the undead." % (victim.user.get_full_name()))
		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_form_kwargs(self):
		kwargs = super(EnterBiteCode, self).get_form_kwargs()
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		self.killer = get_object_or_404(Player, game=self.game, active=True, human=False, user=self.request.user)
		kwargs['killer'] = self.killer
		kwargs['require_location'] = True
		return kwargs

	def get_context_data(self, **kwargs):
		context = super(EnterBiteCode, self).get_context_data(**kwargs)
		return context

class SubmitCodeSMS(APIView):
	@method_decorator(csrf_exempt)
	def post(self, request, *args, **kwargs):
		data = {k: v for (k, v) in request.DATA.iteritems()}
		data['message_timestamp'] = data.pop('message-timestamp', '') # workaround for hyphen in field name
		data['network_code'] = data.pop('network-code', '')
		serializer = NexmoSMSSerializer(data=data)
		if serializer.is_valid():
			data = serializer.object
			games = Game.objects.all().order_by('-start_date')
			for game in games:
				if game.status == "in_progress":
					try:
						phone_number = "%s-%s-%s" % (data['msisdn'][1:4], data['msisdn'][4:7], data['msisdn'][7:11])
						player = Player.objects.get(game=game, user__profile__phone_number=phone_number)
					except Player.DoesNotExist:
						break
					code = data['text'].lower().strip()
					form = BiteCodeForm(data={'bite_code': code}, killer=player)
					# player is the killer
					if form.is_valid():
						kill = form.victim.kill_me(player)
						if kill:
							send_sms_confirmation.delay(player, kill)
							send_death_notification.delay(kill)
						break
					form = AwardCodeForm(data={'code': code}, player=player)
					if form.is_valid():
						with transaction.atomic():
							award = form.award
							award.players.add(player)
							award.save()
							send_sms_confirmation.delay(player, award)
						break
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
		messages.success(self.request, "Code entry accepted!")
		return HttpResponseRedirect(self.game.get_absolute_url())

	def form_invalid(self, form):
		for e in form.non_field_errors():
			messages.error(self.request, e)
		return HttpResponseRedirect(self.game.get_absolute_url())

	def get_form_kwargs(self):
		kwargs = super(SubmitAwardCode, self).get_form_kwargs()
		self.game = get_object_or_404(Game, id=self.kwargs['pk'])
		self.player = get_object_or_404(Player, game=self.game, active=True, user=self.request.user)
		kwargs['player'] = self.player
		return kwargs

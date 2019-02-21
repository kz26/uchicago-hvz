from django.shortcuts import *
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import *
from django.contrib.auth.forms import PasswordResetForm
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.shortcuts import render_to_response
from django.views.generic import DetailView, FormView, TemplateView, UpdateView
from uchicagohvz.game.models import Player
from uchicagohvz.users import forms
from uchicagohvz.users.models import Moderator, Profile
from uchicagohvz.game.templatetags.game_extras import pp_timedelta
from uchicagohvz.game.models import *
from uchicagohvz.webhooks import *
import datetime

# Create your views here.

def login(request):
	return auth_views.login(request, "users/login.html")

def logout(request):
	return auth_views.logout(request, "/")

class RegisterUser(FormView):
	form_class = forms.UserRegistrationForm
	template_name = "users/register.html"

	def form_valid(self, form):
		user = form.save(commit=False)
		user.set_password(user.password)
		user.save()
		return HttpResponseRedirect('/')

	def get_context_data(self, **kwargs):
		context = super(RegisterUser, self).get_context_data(**kwargs)
		return context


class ContactPage(TemplateView):
	template_name = "users/contact.html"

	def get_context_data(self, **kwargs):
		context = super(ContactPage, self).get_context_data(**kwargs)
		context['moderators'] = Moderator.objects.all()
		return context


class ResetPassword(FormView):
	form_class = PasswordResetForm
	template_name = "users/reset_password.html"

	def form_valid(self, form):
		form.save(request=self.request)
		messages.success(self.request, "Password changed successfully.")
		return HttpResponseRedirect('/')

	# def get_context_data(self, **kwargs):
	# 	context = super(ResetPassword, self).get_context_data(**kwargs)
	# 	return context

class ShowProfile(DetailView):
	model = Profile
	template_name = "users/profile.html"

	def get_context_data(self, **kwargs):
		def add(x,y):
			try:
				return x+y
			except TypeError:
				if isinstance( x,datetime.timedelta):
					return x
				elif isinstance(y, datetime.timedelta):
					return y
				else:
					return 0

		def f(t):
			return isinstance(t, datetime.timedelta)

		context = super(ShowProfile, self).get_context_data(**kwargs)
		if self.request.user.is_authenticated():		
			player_list = Player.objects.filter(user=self.request.user)
			total_kills = 0
			total_human_points = 0
			total_zombie_points = 0
			deaths = 0
			lifespans = []
			if player_list:
				for player in player_list:
					total_kills += len(player.kills)
					total_zombie_points += player.zombie_points
					total_human_points += player.human_points
					try:					
						lifespans.append(player.lifespan)
					except:
						pass
					if player.human == False:
						deaths += 1
			
				context['deaths'] = deaths
				context['total_kills'] = total_kills
				context['total_zombie_points'] = total_zombie_points
				context['total_human_points'] = total_human_points
				if len(lifespans) > 0:
					sum = reduce(add, lifespans)
					if sum:
						context['average_lifespan'] = pp_timedelta(sum / len(lifespans))
						context['longest_life'] = pp_timedelta(max(filter(f, lifespans)))
					else:
						context['average_lifespan'] = 0
						context['longest_life'] = 0
				else:
					context['average_lifespan'] = 0
					context['longest_life'] = 0

				context['participation'] = len(player_list)

		return context

class MyAccount(UpdateView):
	form_class = forms.ProfileForm
	template_name = "users/account.html"

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(MyAccount, self).dispatch(request, *args, **kwargs)

	def get_object(self, queryset=None):
		return get_object_or_404(Profile, user=self.request.user)

	def form_valid(self, form):
		user = self.request.user
		current_game = Game.objects.all()[0];
		try:
			current_player = current_game.players.get(user_id = user.id)
		except Player.DoesNotExist:
			current_player = None
		messages.success(self.request, "Account settings updated successfully")
		return super(MyAccount, self).form_valid(form)

	def get_form_kwargs(self):
		kwargs = super(MyAccount, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

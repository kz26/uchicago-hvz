from django.shortcuts import *
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import *
from django.contrib.auth.forms import PasswordResetForm
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.generic import *
from uchicagohvz.users.forms import *
from uchicagohvz.users.models import *
from uchicagohvz.game.models import *
from uchicagohvz.game.templatetags.game_extras import pp_timedelta
import datetime

# Create your views here.

def login(request):
	return auth_views.login(request, "users/login.html")

def logout(request):
	return auth_views.logout(request, "/")

class RegisterUser(FormView):
	form_class = UserRegistrationForm
	template_name = "users/register.html"

	def form_valid(self, form):
		user = form.save(commit=False)
		user.set_password(user.password)
		user.save()
		return HttpResponseRedirect('/')

	def get_context_data(self, **kwargs):
		context = super(RegisterUser, self).get_context_data(**kwargs)
		return context

class ResetPassword(FormView):
	form_class = PasswordResetForm
	template_name = "users/reset_password.html"

	def form_valid(self, form):
		form.save(request=self.request)
		return HttpResponseRedirect('/')

	def get_context_data(self, **kwargs):
		context = super(ResetPassword, self).get_context_data(**kwargs)
		return context

class ShowProfile(DetailView):
	model = Profile
	template_name = "users/profile.html"

	def get_context_data(self, **kwargs):
		def add(x,y): return x+y
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
					lifespans.append(player.lifespan)
					if player.human == False:
						deaths += 1
			
				context['deaths'] = deaths
				context['total_kills'] = total_kills
				context['total_zombie_points'] = total_zombie_points
				context['total_human_points'] = total_human_points
				if len(lifespans) > 0:
					context['average_lifespan'] = pp_timedelta(reduce(add, lifespans) / len(lifespans))
				else:
					context['average_lifespan'] = 0
				context['longest_life'] = pp_timedelta(max(lifespans))
				context['participation'] = len(player_list)

		return context

class UpdateProfile(UpdateView):
	form_class = ProfileForm
	template_name = "users/update_profile.html"

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(UpdateProfile, self).dispatch(request, *args, **kwargs)

	def get_object(self, queryset=None):
		return get_object_or_404(Profile, user=self.request.user)

	def form_valid(self, form):
		messages.success(self.request, "Profile updated successfully.")
		return super(UpdateProfile, self).form_valid(form)

	def get_form_kwargs(self):
		kwargs = super(UpdateProfile, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

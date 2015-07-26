from django.shortcuts import *
from django.http import Http404
from django.conf import settings
from django.core import mail
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib.auth.decorators import *
from django.contrib.auth.forms import PasswordResetForm
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.shortcuts import render_to_response
from django.views.generic import *
from django.views.decorators.csrf import csrf_exempt
from uchicagohvz.users.forms import *
from uchicagohvz.users.models import *
from uchicagohvz.game.models import *
from uchicagohvz.game.templatetags.game_extras import pp_timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
import django.utils.timezone as timezone
import random
import hashlib

# Create your views here.

def send_activation_email(student_number):
	subject = settings.ACTIVATION_MAIL_SUBJECT
	msg = settings.ACTIVATION_MAIL_MSG
	src = settings.DEFAULT_FROM_EMAIL
	dest = student_number + '@campus.ru.ac.za'
	salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
	activation_key = hashlib.sha1(salt+dest).hexdigest()
	key_expires = timezone.now().today() + timezone.timedelta(days=2)
	msg = msg % (activation_key)
	mail.send_mail(subject, msg, src, [dest])
	return (activation_key, key_expires)

def login(request):
	return auth_views.login(request, "users/login.html")

def logout(request):
	return auth_views.logout(request, "/")

class Activate(APIView):
	success_url = '/users/activate/success'
	@method_decorator(csrf_exempt)
	def get(self, *args, **kwargs):
		key = self.request.query_params.get('key', None)
		if key:
			profile = get_object_or_404(Profile, activation_key=key)
			if profile:
				user = profile.user
				user.is_active = True
				user.save()
				profile.activation_key_expires = timezone.now()
				profile.save()
				return HttpResponseRedirect(self.success_url)
		raise Http404("Key does not exist. Please contact the site administrator.")


class RegisterUser(FormView):
	form_class = UserRegistrationForm
	template_name = "users/register.html"

	def form_valid(self, form):
		user = form.save(commit=False)
		user.set_password(user.password)
		user.is_active = False
		user.save()
		(act_key, exp) = send_activation_email(user.username)
		try:
			profile = Profile.objects.get(user=user)
		except:
			profile = Profile(user=user)
		profile.activation_key=act_key
		profile.activation_key_expires=exp
		profile.save()
		return HttpResponseRedirect('/users/register/success')

	def get_context_data(self, **kwargs):
		context = super(RegisterUser, self).get_context_data(**kwargs)
		return context

class UserRegisterSuccess(TemplateView):
	template_name = "registration/register_success.html"

class ActivateSuccess(TemplateView):
	template_name = "registration/activation_success.html"

class ResetPassword(FormView):
	form_class = PasswordResetForm
	template_name = "users/reset_password.html"

	def form_valid(self, form):
		form.save(request=self.request)
		return HttpResponseRedirect('/')

	def get_context_data(self, **kwargs):
		context = super(ResetPassword, self).get_context_data(**kwargs)
		return context

class ResendActivationEmail(FormView):
	form_class = ResendActivationEmailForm
	template_name = "registration/resend_activation.html"
	success_url = '/users/register/success/'
	
	def form_valid(self, form):
		user = get_object_or_404(User, username=form.cleaned_data['username'])
		if user.is_active:
			return HttpResponseRedirect('/')
		profile = None
		try:
			profile = Profile.objects.get(user=user)
		except Profile.DoesNotExist:
			profile = Profile(user=user)
		act, exp = send_activation_email(user.username)
		profile.activation_key = act
		profile.activation_key_expires = exp
		profile.save()
		return HttpResponseRedirect(self.success_url)

class ShowProfile(DetailView):
	model = Profile
	template_name = "users/profile.html"

	def get_context_data(self, **kwargs):
		def add(x,y):
			try:
				return x+y
			except TypeError:
				if isinstance( x, datetime.timedelta ):
					return x
				elif isinstance( y, datetime.timedelta ):
					return y
				else:
					return 0

		def f(t):
			return isinstance( t, datetime.timedelta )

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
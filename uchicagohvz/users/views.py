from django.shortcuts import *
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import *
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.generic import *
from uchicagohvz.users.forms import *

# Create your views here.

def login(request):
	return auth_views.login(request, "users/login.html")

def logout(request):
	return auth_views.logout(request, "/")

class UpdateProfile(UpdateView):
	form_class = ProfileForm
	template_name = "users/profile.html"

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
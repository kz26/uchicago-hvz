from django.shortcuts import render
from django.contrib.auth import views as auth_views

# Create your views here.

def login(request):
	return auth_views.login(request, "users/login.html")
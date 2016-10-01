from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from uchicagohvz.users.models import Profile


# class ProfileAdmin(admin.ModelAdmin):
# 	search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')


class ProfileInline(admin.TabularInline):
	model = Profile


class CustomUserAdmin(UserAdmin):
	inlines = [ProfileInline]

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
# admin.site.register(Profile, ProfileAdmin)

# Register your models here.

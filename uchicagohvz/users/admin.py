from django.contrib import admin
from uchicagohvz.users.models import Profile

class ProfileAdmin(admin.ModelAdmin):
	search_fields = ('user__username', 'user__first_name', 'user__last_name')

admin.site.register(Profile, ProfileAdmin)

# Register your models here.

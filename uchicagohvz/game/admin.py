from django.contrib import admin
from django.conf import settings
from uchicagohvz.game.models import *

# Register your models here.

admin.site.register(Game)

class PlayerAdmin(admin.ModelAdmin):
	list_filter = ('game__name', 'active', 'human', 'dorm', 'renting_gun', 'gun_returned', 'major')
	readonly_fields = ('points',)
	if not settings.DEBUG:
		readonly_fields += ('major',)
	search_fields = ('user__username', 'user__first_name', 'user__last_name', 'bite_code')

class KillAdmin(admin.ModelAdmin):
	list_filter = ('killer__game__name',)
	readonly_fields = ('parent',)
	search_fields = ('killer__user__cnetid', 'killer__user__first_name', 'killer__user__last_name', 
		'victim__user__cnetid', 'victim__user__first_name', 'victim__user__last_name')

admin.site.register(Player, PlayerAdmin)
admin.site.register(Kill, KillAdmin)
admin.site.register(Award)
admin.site.register(HighValueTarget)
admin.site.register(HighValueDorm)
from django.contrib import admin
from uchicagohvz.game.models import *

# Register your models here.

admin.site.register(Game)

class PlayerAdmin(admin.ModelAdmin):
	list_filter = ('game__name', 'active', 'human', 'dorm')
	readonly_fields = ('major',)

class KillAdmin(admin.ModelAdmin):
	list_filter = ('killer__game__name',)
	readonly_fields = ('parent',)

admin.site.register(Player, PlayerAdmin)
admin.site.register(Kill, KillAdmin)
admin.site.register(Award)
admin.site.register(HighValueTarget)
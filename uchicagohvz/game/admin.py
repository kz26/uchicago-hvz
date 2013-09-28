from django.contrib import admin
from uchicagohvz.game.models import *

# Register your models here.

admin.site.register(Game)

class PlayerAdmin(admin.ModelAdmin):
	list_filter = ('game', 'active', 'human', 'dorm')
	readonly_fields = ('major',)

admin.site.register(Player, PlayerAdmin)
admin.site.register(Kill)
admin.site.register(Award)
admin.site.register(HighValueTarget)
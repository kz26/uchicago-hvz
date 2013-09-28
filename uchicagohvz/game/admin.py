from django.contrib import admin
from django import forms
from htmlpurifier.fields import HTMLField
from ckeditor.widgets import CKEditorArea
from uchicagohvz.game.models import *

# Register your models here.

class GameAdminForm(forms.ModelForm):
	class Meta:
		model = Game
	class Media:
		css = {
		'all': ('css/main.css',)
		}

	terms = HTMLField(widget=CKEditorArea())

class GameAdmin(admin.ModelAdmin):
	form = GameAdminForm

admin.site.register(Game, GameAdmin)

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
from django.contrib import admin
from django import forms
from django.conf import settings
from django.http import HttpResponse
from uchicagohvz.game.models import *

# Register your models here.

admin.site.register(Game)

class PlayerAdminForm(forms.ModelForm):
	def clean_squad(self):
		squad = self.cleaned_data.get('squad')
		if squad:
			player_game = self.cleaned_data['game']
			if squad.game != player_game:
				raise forms.ValidationError("Squad game (%s) does not match player game (%s)." % (squad.game.name, player_game.name))
		return squad

class PlayerAdmin(admin.ModelAdmin):
	form = PlayerAdminForm
	list_filter = ('game', 'active', 'human', 'dorm', 'squad', 'new_squad', 'renting_gun', 'gun_requested', 'gun_returned', 'major')
	if not settings.DEBUG:
		readonly_fields = ('major',)
	search_fields = ('user__username', 'user__first_name', 'user__last_name', 'bite_code')
	actions = ['players_to_csv']

	def players_to_csv(ma, request, players):
		response = HttpResponse(content_type='text/plain')
		header = ['NAME', 'USERNAME', 'EMAIL', 'PHONE_NUMBER', 'GAME', 'ACTIVE', 'DORM', 'RENTING_GUN', 'GUN_RETURNED']
		response.write(','.join(header) + '\n')
		for p in players.order_by('user__last_name', 'user__first_name'):
			data = (
				p.user.get_full_name(),
				p.user.username,
				p.user.email,
				p.user.profile.phone_number,
				p.game.name,
				str(p.active),
				p.get_dorm_display(),
				str(p.renting_gun),
				str(p.gun_returned)
			)
			response.write(','.join(data) + '\n')
		return response
	players_to_csv.short_description = 'Export to CSV'

class KillAdminForm(forms.ModelForm):
	def clean_hvd(self):
		hvd = self.cleaned_data.get('hvd')
		if hvd:
			victim = self.cleaned_data['victim']
			kill_date = self.cleaned_data['date']
			if hvd.dorm == victim.dorm and hvd.game == victim.game and hvd.start_date <= kill_date <= hvd.end_date:
				return hvd
			raise forms.ValidationError('HVD game/dorm do not match those of the victim, or kill date out of bounds.')
		else:
			return hvd

	def clean_hvt(self):
		hvt = self.cleaned_data.get('hvt')
		if hvt:
			victim = self.cleaned_data['victim']
			if victim.opt_out_hvt:
				raise forms.ValidationError("%s has opted out of HVT; the selected HVT entry is no longer valid." % (victim.user.get_full_name()))
			kill_date = self.cleaned_data['date']
			if hvt.player == victim and hvt.start_date <= kill_date <= hvt.end_date:
				return hvt
			raise forms.ValidationError('HVT does not match victim, or kill date out of bounds.')
		else:
			return hvt

	def clean(self):
		cleaned_data = super(KillAdminForm, self).clean()
		if cleaned_data['killer'].game != cleaned_data['victim'].game:
			raise forms.ValidationError('killer.game and victim.game do not match.')
		return cleaned_data

class KillAdmin(admin.ModelAdmin):
	form = KillAdminForm
	list_filter = ('killer__game',)
	readonly_fields = ('parent',)
	search_fields = ('killer__user__username', 'killer__user__first_name', 'killer__user__last_name', 
		'victim__user__username', 'victim__user__first_name', 'victim__user__last_name')

class AwardAdminForm(forms.ModelForm):
	def clean_players(self):
		players = self.cleaned_data.get('players', [])
		game = self.cleaned_data.get('game')
		if game:
			for player in players:
				if player.game != game:
					raise forms.ValidationError("%s is part of game %s but this Award is for game %s." % (
						player.user.get_full_name(), player.game.name, game.name)
					)
		return players

class AwardAdmin(admin.ModelAdmin):
	form = AwardAdminForm
	filter_horizontal = ('players',)

class HVTAdminForm(forms.ModelForm):
	def clean_player(self):
		player = self.cleaned_data['player']
		if player.opt_out_hvt:
			raise forms.ValidationError("%s has opted out of HVT. Please choose another player." % (player.user.get_full_name()))
		return player

class HVTAdmin(admin.ModelAdmin):
	form = HVTAdminForm

class MissionAdminForm(forms.ModelForm):
	def clean_awards(self):
		awards = self.cleaned_data.get('awards', [])
		game = self.cleaned_data.get('game')
		if game:
			for award in awards:
				if award.game != game:
					raise forms.ValidationError("%s is part of game %s but this Mission is for game %s." % (
						award.name, award.game.name, game.name)
					)
		return awards

class MissionAdmin(admin.ModelAdmin):
	form = MissionAdminForm
	filter_horizontal = ('awards',)

class MissionPictureAdminForm(forms.ModelForm):
	def clean_players(self):
		players = self.cleaned_data.get('players', [])
		game = self.cleaned_data.get('game')
		if game:
			for player in players:
				if player.game != game:
					raise forms.ValidationError("%s is part of game %s but this Award is for game %s." % (
						player.user.get_full_name(), player.game.name, game.name)
					)
		return players

class MissionPictureAdmin(admin.ModelAdmin):
	form = MissionPictureAdminForm
	filter_horizontal = ('players',)

admin.site.register(Squad)
admin.site.register(New_Squad)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Kill, KillAdmin)
admin.site.register(Award, AwardAdmin)
admin.site.register(HighValueTarget, HVTAdmin)
admin.site.register(HighValueDorm)
admin.site.register(Mission, MissionAdmin)
admin.site.register(MissionPicture, MissionPictureAdmin)
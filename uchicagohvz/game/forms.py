from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.contrib.admin.widgets import FilteredSelectMultiple
from uchicagohvz.game.models import Award, Kill, MissionPicture, New_Squad, Player
from uchicagohvz.webhooks import *

class SquadForm(forms.Form):
	create_squad = forms.CharField(required=False)
	choose_squad = forms.ModelChoiceField(required=False, queryset=New_Squad.objects.none())

	def __init__(self, *args, **kwargs):
		self.game = kwargs.pop('game')
		super(SquadForm, self).__init__(*args, **kwargs)
		self.fields['choose_squad'].queryset = New_Squad.objects.filter(game=self.game)
		self.fields['choose_squad'].widget.attrs['class'] = 'form-control' # for Bootstrap 3
			
	def clean_create_squad(self):
		sn = self.cleaned_data.get('create_squad')
		if sn and New_Squad.objects.filter(game=self.game, name=sn).exists():
			raise forms.ValidationError(
				"There is already a squad named %s. Please join %s or use a different squad name." \
				% (sn, sn))
		return sn

	def clean(self):
		cleaned_data = super(SquadForm, self).clean()
		if not (cleaned_data.get('create_squad') or cleaned_data.get('choose_squad')):
			raise forms.ValidationError(
				"You must either create a squad or join an existing squad.")
		return cleaned_data


class GameRegistrationForm(forms.ModelForm):
	class Meta:
		model = Player
		fields = ('dorm', 'gun_requested', 'opt_out_hvt', 'agree')

	agree = forms.BooleanField()
	

	def __init__(self, *args, **kwargs):
		self.game = kwargs.pop('game')
		super(GameRegistrationForm, self).__init__(*args, **kwargs)
		self.fields['dorm'].queryset = self.game.dorms.all()
		self.fields['dorm'].widget.attrs['class'] = 'form-control' # for Bootstrap 3
		self.fields['dorm'].widget.attrs['required'] = 'required'

def validate_lat(value):
	if not (settings.GAME_SW_BOUND[0] <= value <= settings.GAME_NE_BOUND[0]):
		raise ValidationError('Latitude is outside of game boundaries')

def validate_lng(value):
	if not (settings.GAME_SW_BOUND[1] <= value <= settings.GAME_NE_BOUND[1]):
		raise ValidationError('Longitude is outside of game boundaries')

class BiteCodeForm(forms.Form):
	bite_code = forms.CharField()
	lat = forms.FloatField(required=False, validators=[validate_lat])
	lng = forms.FloatField(required=False, validators=[validate_lng])
	notes = forms.CharField(required=False)

	def __init__(self, *args, **kwargs):
		self.killer = kwargs.pop('killer')
		require_location = kwargs.pop('require_location', False)
		super(BiteCodeForm, self).__init__(*args, **kwargs)
		if require_location:
			self.fields['lat'].required = True
			self.fields['lng'].required = True

	def clean_bite_code(self):
		if not self.killer.active:
			raise forms.ValidationError('Player entering bite code is not activated for this game.')
		if self.killer.human:
			raise forms.ValidationError('Player entering bite code is not a zombie.')
		bite_code = self.cleaned_data['bite_code'].lower().strip()
		try:
			self.victim = Player.objects.get(game=self.killer.game, active=True, bite_code__iexact=bite_code)
		except Player.DoesNotExist:
			raise forms.ValidationError('Invalid bite code entered. Check your spelling and try again.')
		if self.killer.game.status != 'in_progress':
			raise forms.ValidationError('Game is not in progress.')
		if self.victim == self.killer:
			raise forms.ValidationError('You can\'t kill yourself. You\'re already dead, anyway...')
		if not self.victim.human:
			raise forms.ValidationError("%s is already dead!" % (self.victim.bite_code))
		return bite_code

class AnnotateKillForm(forms.ModelForm):
	class Meta:
		model = Kill
		fields = ('lat', 'lng', 'notes')
	lat = forms.FloatField(required=False, validators=[validate_lat])
	lng = forms.FloatField(required=False, validators=[validate_lng])

	def __init__(self, *args, **kwargs):
		super(AnnotateKillForm, self).__init__(*args, **kwargs)

class UploadMissionPictureForm(forms.ModelForm):
	class Meta:
		model = MissionPicture
		fields = ('lat', 'lng', 'picture', 'players')

	players = forms.ModelMultipleChoiceField(required=False, queryset=Player.objects.none(),
		widget=FilteredSelectMultiple(('Players'), False,))
	lat = forms.FloatField(required=False, validators=[validate_lat])
	lng = forms.FloatField(required=False, validators=[validate_lng])
	picture = forms.FileField(required=False)

	def __init__(self, *args, **kwargs):
		self.game = kwargs.pop('game')
		super(UploadMissionPictureForm, self).__init__(*args, **kwargs)
		self.fields['players'].queryset = Player.objects.filter(game=self.game)

class AwardCodeForm(forms.Form):
	code = forms.CharField()

	def __init__(self, *args, **kwargs):
		self.player = kwargs.pop('player')
		super(AwardCodeForm, self).__init__(*args, **kwargs)

	def clean(self):
		if not self.player.active:
			raise forms.ValidationError('Player entering code is not activated for this game.')
		data = super(AwardCodeForm, self).clean()
		code = data.get('code', '').lower().strip()
		if code:
			redeem_types = ['A']
			if self.player.human:
				redeem_types.append('H')
			else:
				redeem_types.append('Z')
			redeem_types = set(redeem_types)
			try:
				self.award = Award.objects.get(game=self.player.game, code__iexact=code)
			except Award.DoesNotExist:
				raise forms.ValidationError('Invalid code entered. Check your spelling and try again.')
			if self.award.game.status != 'in_progress':
				raise forms.ValidationError('Game is not in progress.')
			if not (self.award.redeem_type in redeem_types):
				raise forms.ValidationError('You are not eligible to redeem this code.')
			if self.award.players.filter(id=self.player.id).exists():
				raise forms.ValidationError('You have already redeemed this code.')
			if self.award.players.all().count() >= self.award.redeem_limit:
				raise forms.ValidationError('Sorry, the redemption limit for this code has been reached.')
		return data

class DiscordTagForm(forms.Form):
	tag = forms.CharField()

	def __init__(self, *args, **kwargs):
		self.player = kwargs.pop('player')
		self.user = kwargs.pop('user')
		super(DiscordTagForm, self).__init__(*args, **kwargs)

	def clean(self): 
		data = super(DiscordTagForm, self).clean()
		self.tag = data.get('tag').strip()
		if not "#" in self.tag:
			raise forms.ValidationError("Invalid tag entered, tag must have # and must be of the form Username#1234")
		else:
			tagnums = self.tag.split("#")[1]
			if len(tagnums) != 4:
				raise forms.ValidationError("Invalid tag entered, tag did not contain four numbers after #")
		if self.tag:
			webhook_send_command("!register_player %s %d" %(self.tag, self.player.human))
			self.user.profile.discord_tag = self.tag
			self.user.profile.save()
		return data


class ZombieTextForm(forms.Form):
	message = forms.CharField()

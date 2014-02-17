from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from uchicagohvz.game.models import *

class GameRegistrationForm(forms.ModelForm):
	class Meta:
		model = Player
		fields = ('dorm', 'gun_requested', 'opt_out_hvt', 'agree')

	agree = forms.BooleanField()

	def __init__(self, *args, **kwargs):
		super(GameRegistrationForm, self).__init__(*args, **kwargs)
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

	def __init__(self, *args, **kwargs):
		self.killer = kwargs.pop('killer')
		require_location = kwargs.pop('require_location', False)
		super(BiteCodeForm, self).__init__(*args, **kwargs)
		if require_location:
			self.fields['lat'].required = True
			self.fields['lng'].required = True

	def clean_bite_code(self):
		if self.killer.human:
			raise forms.ValidationError('Player entering bite code is not a zombie.')
		bite_code = self.cleaned_data['bite_code']
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

class AddKillGeotagForm(forms.ModelForm):
	class Meta:
		model = Kill
		fields = ('lat', 'lng')
	lat = forms.FloatField(required=False, validators=[validate_lat])
	lng = forms.FloatField(required=False, validators=[validate_lng])

class AwardCodeForm(forms.Form):
	code = forms.CharField()

	def __init__(self, *args, **kwargs):
		self.player = kwargs.pop('player')
		super(AwardCodeForm, self).__init__(*args, **kwargs)

	def clean(self):
		data = super(AwardCodeForm, self).clean()
		code = data.get('code')
		if code:
			redeem_types = ["A"]
			if self.player.human:
				redeem_types.append("H")
			else:
				redeem_types.append("Z")
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

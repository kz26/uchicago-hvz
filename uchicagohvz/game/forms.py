from django import forms
from uchicagohvz.game.models import *

class GameRegistrationForm(forms.Form):
	dorm = forms.TypedChoiceField(choices=DORMS)
	agree_terms = forms.BooleanField()
	renting_gun = forms.BooleanField(required=False)

	def __init__(self, *args, **kwargs):
		super(GameRegistrationForm, self).__init__(*args, **kwargs)
		self.fields['dorm'].widget.attrs['class'] = "form-control" # for Bootstrap 3
		self.fields['dorm'].widget.attrs['required'] = "required"

class BiteCodeForm(forms.Form):
	bite_code = forms.CharField()

	def __init__(self, *args, **kwargs):
		self.player = kwargs.pop('player')
		super(BiteCodeForm, self).__init__(*args, **kwargs)

	def clean(self):
		data = super(BiteCodeForm, self).clean()
		bite_code = data.get('bite_code')
		if bite_code:
			try:
				self.victim = Player.objects.get(game__id=self.player.game.id, active=True, bite_code=bite_code)
			except Player.DoesNotExist:
				raise forms.ValidationError("Invalid bite code entered.")
			if self.victim.game.status != "in_progress":
				raise forms.ValidationError("Game is not in progress.")
			if not self.victim.human:
				raise forms.ValidationError("%s is already dead!" % (self.victim.user.get_full_name()))
		return data

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
				self.award = Award.objects.get(game__id=self.player.game.id, code=code)
			except Award.DoesNotExist:
				raise forms.ValidationError("Invalid code entered.")
			if self.award.game.status != "in_progress":
				raise forms.ValidationError("Game is not in progress.")
			if self.award.redeem_type not in redeem_types:
				raise forms.ValidationError("You are not eligible to redeem this code.")
			if self.award.players.filter(id=self.player.id):
				raise forms.ValidationError("You have already redeemed this code.")
			if self.award.players.all().count() >= self.award.redeem_limit:
				raise forms.ValidationError("Sorry, the redemption limit for this code has been reached.")
		return data

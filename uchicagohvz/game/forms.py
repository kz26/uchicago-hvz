from django import forms
from uchicagohvz.game.models import *

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
				self.victim = Player.objects.get(game__id=self.player.game.id, active=True, human=True, bite_code=bite_code)
			except Player.DoesNotExist:
				print "No victim with bite code found"
				raise forms.ValidationError("Invalid bite code")
		return data
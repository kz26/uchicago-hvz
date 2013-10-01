from django import forms
from uchicagohvz.users.models import *

class ProfileForm(forms.ModelForm):
	class Meta:
		model = Profile
		exclude = ('user',)

	def __init__(self, *args, **kwargs):
		super(ProfileForm, self).__init__(*args, **kwargs)
		self.fields['phone_carrier'].widget.attrs['class'] = "form-control" # for Bootstrap 3

	def clean(self):
		data = super(ProfileForm, self).clean()
		phone_number = data.get('phone_number')
		phone_carrier = data.get('phone_carrier')
		if phone_number and not phone_carrier:
			self._errors["phone_carrier"] = self.error_class(["Carrier must be specified."])
		if not phone_number:
			data['phone_carrier'] = ""
			data['subscribe_death_notifications'] = False
		return data
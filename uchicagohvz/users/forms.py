from django import forms
from uchicagohvz.users.models import *
from uchicagohvz.game.models import Game, Player

class ProfileForm(forms.ModelForm):

	ZOMBIES_LISTHOST_HELP_INACTIVE = """
		Note: We will only send at most one email per day via this listhost!  Subscribing to this listhost is virtually 
		necessary in order to know when the game ends, when safe zones change, and keep up with any official announcements.
		If you unsubscribe, please also email zombies-request@lists.uchicago.edu to let us know.
	"""

	ZOMBIES_LISTHOST_HELP_ACTIVE = """
		Note: You cannot unsubscribe from the Zombies listhost while you are part of a game that is still in progress. Don't worry,
		we won't spam you! We will only send at most one email per day via this listhost! Subscribing to this listhost is virtually 
		necessary in order to know when the game ends, when safe zones change, and keep up with any official announcements.
	"""

	class Meta:
		model = Profile
		exclude = ('user',)

	def __init__(self, *args, **kwargs):
		self.user = kwargs.pop('user')
		super(ProfileForm, self).__init__(*args, **kwargs)
		self.fields['phone_carrier'].widget.attrs['class'] = 'form-control' # for Bootstrap 3
		if Player.objects.filter(user=self.user, game__in=Game.objects.games_in_progress(), active=True).count():
			self.force_subscribe_zombies = True
			self.fields['subscribe_zombies_listhost'].widget.attrs['disabled'] = 'disabled'
			self.fields['subscribe_zombies_listhost'].help_text = self.ZOMBIES_LISTHOST_HELP_ACTIVE
		else:
			self.fields['subscribe_zombies_listhost'].help_text = self.ZOMBIES_LISTHOST_HELP_INACTIVE
			self.force_subscribe_zombies = False

	def clean(self):
		data = super(ProfileForm, self).clean()
		phone_number = data.get('phone_number')
		phone_carrier = data.get('phone_carrier')
		if phone_number and not phone_carrier:
			self._errors["phone_carrier"] = self.error_class(["Carrier must be specified."])
		if not phone_number:
			data['phone_carrier'] = ''
			data['subscribe_death_notifications'] = False
		if self.force_subscribe_zombies:
			data['subscribe_zombies_listhost'] = True
		return data
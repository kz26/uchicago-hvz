from .models import Game
from uchicagohvz.users.mailing_list import MailgunHookBase

from django.shortcuts import get_object_or_404


class HZMailingListBase(MailgunHookBase):

	def get_to_addrs(self):
		raise NotImplementedError()

	def post(self, request, *args, **kwargs):
		self.game = get_object_or_404(Game, id=kwargs['pk'])	
		return super(HZMailingListBase, self).post(request, *args, **kwargs)

class HumansMailingList(HZMailingListBase):
	def get_listhost_id(self):
		return "%s Humans <https://www.uchicagohvz.org%s>" % (self.game.name, self.game.get_absolute_url())

	def get_listhost_name(self):
		return "%s Humans" % (self.game.name)

	def get_listhost_address(self):
		return self.game.humans_listhost_address

	def get_to_addrs(self):
		return tuple(self.game.players.filter(active=True, user__profile__subscribe_chatter_listhost=True, human=True) \
			.values_list('user__email', flat=True))


class ZombiesMailingList(HZMailingListBase):
	def get_listhost_id(self):
		return "%s Zombies <https://www.uchicagohvz.org%s>" % (self.game.name, self.game.get_absolute_url())

	def get_listhost_name(self):
		return "%s Zombies" % (self.game.name)

	def get_listhost_address(self):
		return self.game.zombies_listhost_address

	def get_to_addrs(self):
		return tuple(self.game.players.filter(active=True, user__profile__subscribe_chatter_listhost=True, human=False) \
			.values_list('user__email', flat=True))

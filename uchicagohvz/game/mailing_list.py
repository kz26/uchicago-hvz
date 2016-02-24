from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.exceptions import PermissionDenied

from .models import Game
from uchicagohvz.users.mailing_list import MailgunHookBase


class HZMailingListBase(MailgunHookBase):
	
	anonymize_from = True

	def get_to_addrs(self):
		raise NotImplementedError()

	def post(self, request, *args, **kwargs):
		self.game = get_object_or_404(Game, id=kwargs['pk'])
		if self.game.status == 'in_progress':
			return super(HZMailingListBase, self).post(request, *args, **kwargs)
		else:
			raise PermissionDenied(detail="Game %s is not currently active." % self.game.name)

class HumansMailingList(HZMailingListBase):

	def get_listhost_name(self):
		return "%s Humans" % (self.game.name)

	def get_listhost_address(self):
		return self.game.humans_listhost_address

	def get_to_addrs(self):
		return tuple(self.game.players.filter(active=True, user__profile__subscribe_chatter_listhost=True) \
			.filter(Q(human=True) | Q(user__is_superuser=True)).distinct() \
			.values_list('user__email', flat=True))


class ZombiesMailingList(HZMailingListBase):
	
	def get_listhost_name(self):
		return "%s Zombies" % (self.game.name)

	def get_listhost_address(self):
		return self.game.zombies_listhost_address

	def get_to_addrs(self):
		return tuple(self.game.players.filter(active=True, user__profile__subscribe_chatter_listhost=True) \
			.filter(Q(human=False) | Q(user__is_superuser=True)).distinct() \
			.values_list('user__email', flat=True))

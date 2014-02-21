from django import template
from django.utils.safestring import mark_safe
from uchicagohvz.game.models import *

register = template.Library()

@register.filter
def award_colorize(award):
	if award.redeem_type == 'H':
		return mark_safe("<span class='text-success'>%s</span>" % (award.name))
	elif award.redeem_type == 'Z':
		return mark_safe("<span class='text-danger'>%s</span>" % (award.name))
	else:
		return award.name


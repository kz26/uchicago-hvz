from django import template
from django.utils.safestring import mark_safe
from uchicagohvz.game.models import *

register = template.Library()

@register.filter
def pp_timedelta(td):
	"""
	Pretty-prints a timedelta representation a duration
	"""
	hours, remainder = divmod(td.seconds, 3600)
	minutes, seconds = divmod(remainder, 60)
	return "%s days, %s hours, %s minutes, %s seconds" % (td.days, hours, minutes, seconds)


@register.filter
def award_colorize(award):
	if award.redeem_type == 'H':
		return mark_safe("<span class='text-success'>%s</span>" % (award.name))
	elif award.redeem_type == 'Z':
		return mark_safe("<span class='text-danger'>%s</span>" % (award.name))
	else:
		return award.name


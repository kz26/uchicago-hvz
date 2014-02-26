from rest_framework import serializers
from uchicagohvz.game.models import *

class KillSerializer(serializers.ModelSerializer):
	class Meta:
		model = Kill
		fields = ('pk', 'killer', 'victim', 'location', 'date', 'points')

	killer = serializers.SerializerMethodField('get_killer')
	victim = serializers.SerializerMethodField('get_victim')
	location = serializers.SerializerMethodField('get_location')

	def get_killer(self, obj):
		return obj.killer.display_name

	def get_victim(self, obj):
		return obj.victim.display_name

	def get_location(self, obj):
		if not (obj.lat and obj.lng):
			return None
		return (obj.lat, obj.lng)


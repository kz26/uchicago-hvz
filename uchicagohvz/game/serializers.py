from rest_framework import serializers
from uchicagohvz.game.models import *

class KillSerializer(serializers.ModelSerializer):
	class Meta:
		model = Kill
		fields = ('id', 'killer', 'victim', 'location', 'date', 'points')

	killer = serializers.SerializerMethodField()
	victim = serializers.SerializerMethodField()
	location = serializers.SerializerMethodField()

	def get_killer(self, obj):
		return obj.killer.display_name

	def get_victim(self, obj):
		return obj.victim.display_name

	def get_location(self, obj):
		if not obj.pos:
			return None
		return (obj.pos.latitude, obj.pos.longitude)

class MissionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Mission
		fields = ('id', 'name', 'end_date', 'img', 'location', 'rtype')

	location = serializers.SerializerMethodField()
	rtype = serializers.SerializerMethodField()

	def get_location(self, obj):
		if not obj.pos:
			return None
		return (obj.pos.latitude, obj.pos.longitude)

	def get_rtype(self, obj):
		return obj.def_redeem_type

class EmailSerializer(serializers.ModelSerializer)
	class Meta:
		model = Player
		fields = ('email', )

	email = serializers.SerializerMethodField()

	def get_email(self, obj):
		return obj.user__email


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
		if not (obj.lat and obj.lng):
			return None
		return (obj.lat, obj.lng)

class PictureSerializer(serializers.ModelSerializer):
	class Meta:
		model = MissionPicture
		fields = ('picture', 'location', 'date', 'points')

	picture = serializers.SerializerMethodField()
	location = serializers.SerializerMethodField()

	def get_picture(self, obj):
		return obj.picture.url

	def get_location(self, obj):
		if not (obj.lat and obj.lng):
			return None
		return (obj.lat, obj.lng)
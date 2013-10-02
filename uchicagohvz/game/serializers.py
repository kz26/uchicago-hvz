from rest_framework import serializers

class NexmoSMSSerializer(serializers.Serializer):
	type = serializers.CharField()
	to = serializers.CharField()
	msisdn = serializers.CharField()
	network_code = serializers.CharField(required=False)
	messageId = serializers.CharField()
	message_timestamp = serializers.DateTimeField()
	text = serializers.CharField()
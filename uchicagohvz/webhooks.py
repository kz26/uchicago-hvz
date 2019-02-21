import requests
from django.conf import settings

def webhook_send_command(command):
	data = {}
	data['content'] = command
	url = "https://discordapp.com/api/webhooks/" + settings.DISCORD_WEBHOOK_KEY
	r = requests.post(url, json=data)
	

import requests

def webhook_register_user(tag, human):
	command = "!register_player %s %d" %(tag, human)
	data = {}
	data['content'] = command
	r = requests.post("https://discordapp.com/api/webhooks/541665497008046090/0FnekImVHLqypEWKzkQQ21WIZS4-Q7HT3wH_F0p0HlrOzigrJCjETc3DFM2fxwQGqRGq", json=data)

def webhook_kill_player(tag):
	command = "!record_death %s" %(tag)
	data = {}
	data['content'] = command
	r = requests.post("https://discordapp.com/api/webhooks/541665497008046090/0FnekImVHLqypEWKzkQQ21WIZS4-Q7HT3wH_F0p0HlrOzigrJCjETc3DFM2fxwQGqRGq", json=data)

def webhook_new_game():
	command = "!reset_roles"
	data = {}
	data['content'] = command
	r = requests.post("https://discordapp.com/api/webhooks/541665497008046090/0FnekImVHLqypEWKzkQQ21WIZS4-Q7HT3wH_F0p0HlrOzigrJCjETc3DFM2fxwQGqRGq", json=data)
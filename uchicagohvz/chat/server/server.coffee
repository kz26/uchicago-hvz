express = require 'express'
http = require 'http'
moment = require 'moment'
sockjs = require 'sockjs'

app = express()
httpServer = http.createServer app
httpServer.listen 36452, '127.0.0.1'

class ChatServer
	constructor: (@hs) -> # takes an HTTP server object
		@server = sockjs.createServer {
			prefix: '/chat',
			log: (severity, message) ->
				if severity == 'error'
					console.log message
		}
		@lobby = []
		@hs.installHandlers(@server)

		@server.on 'connection', (conn) ->
			conn.on 'data', (data) ->
				@data conn, data

			conn.on 'auth', (data) ->
				@auth conn, data

	@writeJSON: (conn, data) ->
		conn.write JSON.stringify(data)
	
	data: (conn, data) =>
		data = JSON.parse(data)
		if data.type?
			conn.emit data.type, data
		
	broadcast: (data) =>
		for conn in @lobby
			@writeJSON conn, data

	auth: (conn, authData) =>
		options = {
			host: '127.0.0.1',
			port: 8000,
			headers: {
				Host: 'www.uchicagohvz.org',
				Cookie: "sessionid=#{ key }"
			},
			path: '/chat/auth/'
		}

		http.get options, (res) =>
			body = ''
			if res.statusCode == 200
				res.on 'data', (chunk) =>
					body += chunk
				res.on 'end', =>
					conn.userObject JSON.parse(body)

					conn.on 'chat', (data) =>
						@chat conn, data

					conn.on 'close', =>
						@removeUser conn

	chat: (conn, data) =>
		@broadcast {type: chat, message: data.message}

	removeUser: (conn) =>
		@lobby = @lobby.filter (v) ->
			return v.session_id == conn.session_id

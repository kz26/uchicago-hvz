express = require 'express'
http = require 'http'
moment = require 'moment'
sockjs = require 'sockjs'


class ChatServer
	constructor: (httpServer) -> # takes an HTTP server object
		@server = sockjs.createServer {
			prefix: '/chat',
			log: (severity, message) ->
				if severity == 'error'
					console.log message
		}
		@lobby = []
		@server.installHandlers(httpServer)

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
		if data.room?
			for conn in @lobby
				if data.room in conn.userObject.rooms
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
					# userObject should contain:
					# uid: unique user ID
					# name: user's full name, used for logging purposes
					# rooms, a list of rooms the user should be in
					conn.userObject = JSON.parse(body)

					conn.on 'chat', (data) =>
						@chat conn, data

					conn.on 'close', =>
						@removeUser conn

	chat: (conn, data) =>
		if conn.userObject.rooms.length == 1
			data.room = conn.userObject.room[0]
		@broadcast conn, data
		@log conn, data

	updateUserRooms: (uid, roomList) =>
		for conn, i in @lobby
			if conn.userObject.uid == uid
				conn.userObject.rooms = roomList

	removeUser: (conn) =>
		@lobby = @lobby.filter (v) ->
			return v.session_id != conn.session_id

	log: (conn, data) =>
		console.log "[#{ moment.now() }] #{ conn.userObject.name }: #{ JSON.stringify(data) }"

app = express()
app.use express.json()
app.use express.urlencoded()


httpServer = http.createServer app
httpServer.listen 36452, '127.0.0.1'
chatServer = new ChatServer(httpServer)

app.post '/admin/updateUserRooms', (req, res) ->
	chatServer.updateUserRooms(req.body.uid, req.body.rooms)
	res.send 200

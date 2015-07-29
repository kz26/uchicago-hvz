pkg = require './package.json'
express = require 'express'
http = require 'http'
moment = require 'moment'
sockjs = require 'sockjs'
request = require 'request'

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

		@server.on 'connection', (conn) =>
			conn.writeJSON = (data) ->
				conn.write JSON.stringify(data)
			conn.on 'data', (data) =>
				@constructor.emitData conn, data

			conn.on 'auth', (data) =>
				@auth conn, data

	@emitData: (conn, data) ->
		data = JSON.parse(data)
		if data.type?
			conn.emit data.type, data

	broadcast: (data) ->
		if data.room?
			for conn in @lobby
				if data.room in conn.userObject.rooms
					conn.writeJSON data

	auth: (conn, authData) ->
		# authData object needs to contain gameID and sessionid
		request.get {
			uri: "https://127.0.0.1:8080/game/#{ authData.gameID }/chat/auth/",
			headers: {
				'User-Agent': "#{ pkg.name }/#{ pkg.version }",
				Host: 'hvz.rucus.me',
				Cookie: "sessionid=#{ authData.sessionid }"
			},
			json: true
		}, (err, res, body) =>
			if res.statusCode == 200
				# returned userObject needs to contain uid, name, rooms list
				conn.userObject = body
				conn.on 'chat', (data) =>
					@chat conn, data
				conn.on 'close', =>
					@removeConn conn
					@broadcast {type: 'announce', announce: '#{ authData.name } has left the room.'}
				@lobby.push conn
				conn.writeJSON {type: 'authenticated'}
				@broadcast {type: 'announce', announce: '#{ authData.name } has entered the fray'}

	chat: (conn, data) ->
		if conn.userObject.rooms.length == 1
			data.room = conn.userObject.rooms[0]
		@broadcast data
		@log conn, data

	updateUserRooms: (uid, roomList) ->
		for conn, i in @lobby
			if conn.userObject.uid == uid
				conn.userObject.rooms = roomList
				conn.writeJSON {type: 'refresh'}

	removeConn: (conn) ->
		@lobby = @lobby.filter (v) ->
			return v.id != conn.id

	log: (conn, data) ->
		console.log "[#{ moment().format('DD/MM/YYYY hh:mm:ss A') }] #{ conn.userObject.name }: #{ JSON.stringify(data) }"

app = express()
app.use express.json()


httpServer = http.createServer app
httpServer.listen 36452, '0.0.0.0'
chatServer = new ChatServer(httpServer)

app.post '/admin/updateUserRooms', (req, res) ->
	chatServer.updateUserRooms(req.body.uid, req.body.rooms)
	res.send 200

chatevents = null

addmsg = (type, msg) ->
  $("#chat").append msg

waitForMsg = ->
  $.ajax
    type: "GET"
    url: "/hivemind/chatslave"
    async: true
    cache: false
    data:
      action: "poll"
    timeout: 50000
    success: (data) ->
      addmsg("new", data)
      setTimeout(waitForMsg, 3000)
    error: (XMLHttpRequest, textStatus, errorThrown) ->
      addmsg("error", textStatus + " (" + errorThrown + ")")
      setTimeout(waitForMsg, 15000)

sendMsg = ->
  $.ajax
    type: "POST"
    url: "/hivemind/publish"
    async: true
    cache: false
    data:
      action: "msg"
      msg: $("#chatbox").val()
    success: ->
      $("#chatbox").val ""

$(document).ready () ->
  $("#chatbox").keypress (e) ->
    if e.which == 13
      sendMsg()
  $("#chatbox_button").mousedown (e) ->
    sendMsg()
  chatevents = new EventSource('/hivemind/sseslave')
  chatevents.onmessage = (e) ->
    addmsg('msg', 'System: ' + e.data + '\n')
  chatevents.onerror = ->
    addmsg('err', 'err\n')
  #waitForMsg()

Tornado-Redis-Chat & Socket.io-Redis-Chat
==================

## Tornado-Redis-Chat
A multi-room chat application based on Tornado and Redis.

	sudo pip install tornado
	sudo pip install git+https://github.com/evilkost/brukva.git
	git clone https://github.com/BeginMan/webchat.git
	python app.py --port=8888


## Socket.io-Redis-Chat
Webchat,android,iOS chat system based on socket.io and redis.

Requirements:

- android: [AndroidAsync, Asynchronous socket, http (client+server), websocket, and socket.io library for android. Based on nio, not threads.](https://github.com/koush/AndroidAsync)
- iOS: [AZSocketIO, A socket.io client for objective-c. Cocoapods-friendly. Appledocs. Built of AFNetworking and SocketRocket. Websockets + XHR.](https://github.com/lukabernardi/AZSocketIO)

Node modules:

- redis or hiredis
- socket.io

Then

	git clone https://github.com/BeginMan/webchat.git
	node chat-server.js




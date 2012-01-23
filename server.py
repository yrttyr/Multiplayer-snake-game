#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process

from gevent import sleep, getcurrent
from ws4py.server.geventserver import WebSocketServer
from ws4py.server.wsgi.middleware import WebSocketHandler

def send(self, data):
    data = protocol.encode(data)
    super(WebSocketHandler, self).send(data)
WebSocketHandler.send = send

import player
from sender import protocol
from sender.base import Subscriber

def http_server():
    import SimpleHTTPServer
    import SocketServer
    import socket

    class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.path = '/client' + self.path
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    class TCPServer(SocketServer.TCPServer):
        allow_reuse_address = True

    httpd = TCPServer(('127.0.0.1', 9923), MyHandler)
    httpd.serve_forever()

p = Process(target=http_server)
p.daemon = True
p.start()

def start():
    server = WebSocketServer(('127.0.0.1', 8080), websocket_app)
    server.serve_forever()

def websocket_app(ws, t):
    ws.subscriber = Subscriber(ws)
    while True:
        data = ws.receive()
        if data:
            fn, args = protocol.decode(ws.subscriber, data)
            fn(ws.subscriber, *args)
        else:
            ws.subscriber = None
            break

class Subscriber(Subscriber):
    def call(self):
        self.subscribe('GamesList')
        self.subscribe('MapsList')
        self.subscribe(player.Player())

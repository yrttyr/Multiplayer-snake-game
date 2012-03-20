#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process

from ws4py.server import geventserver

from sender.base import Subscriber
import player

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

class Subscriber(Subscriber):
    def call(self):
        self.subscribe('GamesList')
        self.subscribe('MapsList')
        self.subscribe(player.Player())

class WebSocket(geventserver.WebSocket):
    def opened(self):
        self.subscriber = Subscriber(self)

    def received_message(self, message):
        self.subscriber.receive(message.data)

    def closed(self, code, reason=None):
        self.subscriber.kill()
        del self.subscriber

server = geventserver.WebSocketServer(('127.0.0.1', 8080),
                                      websocket_class=WebSocket)
server.serve_forever()

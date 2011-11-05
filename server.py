#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process

from gevent import sleep, getcurrent
from ws4py.server.geventserver import WebSocketServer

import sender
import player

def http_server():
    import SimpleHTTPServer
    import SocketServer

    class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.path = '/client' + self.path
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    httpd = SocketServer.TCPServer(('127.0.0.1', 9923), MyHandler)
    httpd.serve_forever()

p = Process(target=http_server)
p.daemon = True
p.start()

def start():
    server = WebSocketServer(('127.0.0.1', 8080), websocket_app)
    try:
        server.serve_forever()
    except:
        server.kill()
        raise

def websocket_app(ws, t):
    ws.subscriber = Subscriber(ws)
    while True:
        data = ws.receive()
        if data:
            ws.subscriber.recv(data)
        else:
            ws.subscriber = None
            break
    print 'ws del'

class Subscriber(sender.Subscriber):
    def call(self):
        self.subscribe('GamesList')
        self.subscribe('MapsList')
        self.subscribe(player.Player())

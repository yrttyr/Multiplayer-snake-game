#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Process

from gevent import sleep, getcurrent
#from gevent.http import HTTPServer
from ws4py.server.geventserver import WebSocketServer
#from geventwebsocket.handler import WebSocketHandler
#import json

#import player
import sender

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
    server.serve_forever()

def websocket_app(ws, t):
    ws.subscriber = Subscriber(ws)
    #try:
    while True:
        data = ws.receive()
        if data:
            ws.subscriber.recv(data)
        else:
            print('ws.websocket_closed')
            break
   # except IOError:
    print 'ws del'
    #ws.player.kill()

import player

class Subscriber(sender.Subscriber):
    def call(self):
        self.subscribe('GamesList')
        self.subscribe('MapsList')
        #self.player = player.Player()
        self.subscribe(player.Player())

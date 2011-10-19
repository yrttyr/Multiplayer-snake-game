#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

#from game import sender#, Game
from sender import sender#, Game

#import game
 #////////////////

@sender.send_cls()
class Player(object):
    tmp = 87, 68, 83, 65
    def __init__(self):
        self.snake = None
        self.game = None
        self.start_coord = ()

    @sender.recv_meth()
    def create_map(self, sub):
        map_ = sub.get_sendobj('GamesList').add_map()
        sub.subscribe(map_)

    @sender.recv_meth()
    def create_game(self, sub, key):
        game = sub.get_sendobj('GamesList').add_game(key)
        self.connect_game(sub, game)

    @sender.recv_meth()
    def connect_game(self, sub, game):         #нужен тест, что это именно гаме
        sub.subscribe(game)
        self.game = sub.get_sendobj('Game')
        self.snake = None
        self.start_coord = ()

    @sender.recv_meth()
    def set_start_coord(self, sub, x, y):
        select_mapobj = self.game.gamemap['ground'][(x, y)].obj
        if getattr(select_mapobj, 'start_pos', False):
            self.start_coord = x, y

    @sender.recv_meth()
    def set_rotate(self, sub, keycode):
        print 'set_rotate', keycode
        try:
            if self.snake:
                self.snake.rotation = self.tmp.index(keycode)
            elif self.game and self.start_coord:
                self.create_snake(self.tmp.index(keycode))
        except ValueError:
            pass

    def create_snake(self, direct):
        self.snake = self.game.add_player(self.start_coord, direct)

    def kill(self):
        self.connect.player = None
        self.connect = None

    def send_start(self):
        pass

    def __del__(self):
        print('player del')

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sender import sender
from weakref import ref

@sender.send_cls()
class Player(object):
    tmp = 87, 68, 83, 65

    def __init__(self):
        self.clear()

    def clear(self):
        self._snake = None
        #self.game = None
        self.start_coord = ()

    @property
    def snake(self):
        if self._snake:
            return self._snake()
        return None

    @snake.setter
    def snake(self, obj):
        self._snake = ref(obj)

    @snake.deleter
    def snake(self):
        self._snake = None

    @sender.recv_meth()
    def set_start_coord(self, sub, x, y):
        game = sub.get_sendobj('Game')
        select_mapobj = game.gamemap['ground'][(x, y)].obj
        if getattr(select_mapobj, 'start_pos', False):
            self.start_coord = x, y

    @sender.recv_meth()
    def set_rotate(self, sub, keycode):
        print 'set_rotate', keycode
        try:
            direct = self.tmp.index(keycode)
        except ValueError:
            direct = 0

        if self.snake:
            self.snake.rotation = direct
        elif 'Game' in sub.send_obj and self.start_coord:
            game = sub.get_sendobj('Game')
            self.snake = game.add_player(self.start_coord, direct)

    def kill(self):
        self.connect.player = None
        self.connect = None

    def send_start(self):
        pass

    def __del__(self):
        print('player del')

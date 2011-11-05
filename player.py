#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sender import sender
from weakref import ref

@sender.send_cls()
class Player(object):
    tmp = 87, 68, 83, 65

    def clear(self, game):
        self._snake = None
        self.game = game
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
        select_mapobj = self.game.gamemap['ground'][(x, y)].obj
        if getattr(select_mapobj, 'start_pos', False):
            self.start_coord = x, y

    @sender.recv_meth()
    def set_rotate(self, sub, keycode):
        print 'set_rotate', keycode
        try:
            direct = self.tmp.index(keycode)
        except ValueError:
            return

        if self.snake and self.snake.alive:
            self.snake.rotation = direct
        elif self.snake and not self.snake.alive:
            self.snake.rotation = direct
            self.snake.start(self.start_coord)
        elif self.game and self.start_coord:
            self.game = sub.get_sendobj('Game')
            self.snake = self.game.add_snake(self.start_coord, direct)

    def kill(self):
        self.connect.player = None
        self.connect = None

    def __del__(self):
        print('player del')
        if self.snake:
            self.game.remove_snake(self.snake)

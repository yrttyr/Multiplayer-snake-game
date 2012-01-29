#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import ref

from sender import public
from sender.base import WrapperUnique

@public.send_cls(wrapper=WrapperUnique)
class Player(object):
    send_attrs = 'scores',
    tmp = 87, 68, 83, 65

    def __init__(self):
        self.start_coord = 0, 0

    def new_game(self, snake):
        self.snake = snake
        self.scores = 0

    def scores_contr(self, value):
        self.scores += value

    @public.recv_meth()
    def set_start_coord(self, sub, x, y):
        self.start_coord = x, y

    @public.recv_meth()
    def set_rotate(self, sub, keycode):
        try:
            direct = self.tmp.index(keycode)
        except ValueError:
            return

        self.snake.rotation = direct
        if not self.snake.alive:
            self.snake.start(self.start_coord)

    def __del__(self):
        print('player del')
        self.clear()

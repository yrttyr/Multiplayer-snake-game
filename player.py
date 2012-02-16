#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import ref

from sender import public
from sender.base import WrapperUnique

@public.send_cls(wrapper=WrapperUnique)
class Player(object):
    send_attrs = 'scores',

    def __init__(self):
        self.start_coord = 0, 0

    def new_game(self, snake):
        self.snake = snake
        self.scores = 0

    def end_game(self):
        self.snake.kill()
        del self.snake

    def scores_contr(self, value):
        self.scores += value

    @public.recv_meth()
    def set_start_coord(self, sub, x, y):
        self.start_coord = x, y

    @public.recv_meth()
    def set_rotate(self, sub, rotate):
        if 0 <= rotate <= 3:
            self.snake.rotation = rotate
            if not self.snake.alive:
                self.snake.start(self.start_coord)

    def __del__(self):
        print('player del')

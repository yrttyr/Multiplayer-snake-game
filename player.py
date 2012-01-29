#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import ref

from sender import public
from sender.base import WrapperUnique

from game import MaxplayerError

@public.send_cls(wrapper=WrapperUnique)
class Player(object):
    send_attrs = 'scores',
    tmp = 87, 68, 83, 65

    def __init__(self):pass

    def setdata(self, game):
        self.clear()
        self.snake = None
        self.game = game
        self.start_coord = ()
        self.scores = 0

    def clear(self):
        if hasattr(self, 'snake') and self.snake:
            self.game.remove_snake(self.snake)

    def scores_contr(self, value):
        self.scores += value

    @public.recv_meth()
    def set_start_coord(self, sub, x, y):
        select_mapobj = self.game.gamemap['ground'][(x, y)].obj
        if getattr(select_mapobj, 'start_pos', False):
            self.start_coord = x, y

    @public.recv_meth()
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
            try:
                self.snake = self.game.add_snake(self.start_coord, direct,
                                                 self.scores_contr)
            except MaxplayerError:
                pass

    def __del__(self):
        print('player del')
        self.clear()

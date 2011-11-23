#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import ref

import sender

@sender.send_cls()
class Player(object):
    tmp = 87, 68, 83, 65

    def clear(self, game):
        self.snake = None
        self.game = game
        self.start_coord = ()
        self.scores = Scores(self)

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
            snake = self.game.add_snake(self.start_coord, direct,
                                        self.scores)
            if snake:
                self.snake = snake
                self.send_score(_send_to='Game')

    @sender.send_meth('scores')
    def send_score(self):
        if self.snake:
            return self.snake.indef, self.scores.get()

    def __del__(self):
        print('player del')
        if self.snake:
            self.game.remove_snake(self.snake)

class Scores(object):
    __slots__ = ('_val', '_player')

    def send(fn):
        def iner(self, *args, **kwars):
            fn(self, *args, **kwars)
            self._player().send_score(_send_to='Game')
        return iner

    @send
    def __init__(self, player):
        self._val = 0
        self._player = ref(player)

    def get(self):
        return self._val

    @send
    def add(self, n):
        self._val += n

    @send
    def sub(self, n):
        self._val -= n

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import ref

import sender

from game import MaxplayerError

@sender.send_cls()
class Player(object):
    tmp = 87, 68, 83, 65

    def setdata(self, game):
        self.clear()
        self.snake = None
        self.game = game
        self.start_coord = ()
        self.scores = None

    def clear(self):
        if hasattr(self, 'snake') and self.snake:
            self.game.remove_snake(self.snake)

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
            try:
                self.snake, self.scores = \
                    self.game.add_snake(self.start_coord, direct)
            except MaxplayerError:
                pass

    def __del__(self):
        print('player del')
        self.clear()

class Scores(object):
    def send(fn):
        def iner(self, *args, **kwars):
            fn(self, *args, **kwars)
            self.send_score(_send_to=self.game)
        return iner

    @sender.send_fun('scores')
    def send_score(self):
        return self.player_id, self._val

    @send
    def setdata(self, game, player_id):
        self._val = 0
        self.player_id = player_id
        self.game = sender.wrappers[id(game)]

    @send
    def add(self, n):
        self._val += n

    @send
    def sub(self, n):
        self._val -= n

    @send
    def __del__(self):
        print 'score del'
        self._val = ''

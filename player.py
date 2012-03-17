#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import ref

from sender import public
from sender.base import WrapperUnique

@public.send_cls(wrapper=WrapperUnique)
class Player(object):
    send_attrs = 'scores',

    def __init__(self):
        self.scores = 0

    @property
    def wrapper(self):
        return self._wrapper

    @wrapper.setter
    def wrapper(self, wrapper_constr):
        self._wrapper = wrapper_constr(self)

    @wrapper.deleter
    def wrapper(self):
        self._wrapper.kill()
        del self._wrapper

    @public.recv_meth()
    def set_coord(self, sub, x, y):
        self.wrapper.set_coord(x, y)

    @public.recv_meth()
    def set_rotate(self, sub, rotate):
        self.wrapper.set_rotate(rotate)

    @public.recv_meth()
    def set_parameter(self, sub, name, value):
        self.wrapper.set_parameter(name, value)

class GameWrapper(object):
    def __init__(self, snake_constr, player):
        self.player = player
        player.scores = 0
        self.start_coord = 0, 0
        self.snake = snake_constr(self.scores_contr)

    def kill(self):
        self.snake.kill()
        del self.snake
        del self.player

    def set_coord(self, x, y):
        self.start_coord = x, y

    def set_rotate(self, rotate):
        if 0 <= rotate <= 3:
            self.snake.rotation = rotate
            if not self.snake.alive:
                self.snake.start(self.start_coord)

    def set_parameter(self, name, value):
        pass

    def scores_contr(self, value):
        self.player.scores += value

class MapEditorWrapper(object):
    allow_parameter = set(['tile', 'size'])

    def __init__(self, mapeditor, player):
        self.mapeditor = mapeditor
        self.player = player
        self.coord = 0, 0
        self.tile = 0

    def kill(self):
        del self.player

    def set_coord(self, x, y):
        self.coord = x, y
        self.mapeditor.objects[self.tile].create_object([self.coord])

    def set_rotate(self, rotate):
        pass

    def set_parameter(self, name, value):
        if name in self.allow_parameter:
            if name == 'size':
                self.mapeditor.gamemap.set_size(*value)
            else:
                setattr(self, name, value)

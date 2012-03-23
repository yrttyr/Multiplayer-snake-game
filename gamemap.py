#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import itertools
from UserDict import IterableUserDict

from sender import public, objects
from sender.base import WrapperUnique

@public.send_cls(wrapper=WrapperUnique)
class Gamemap(object, IterableUserDict):
    def __init__(self, x, y):
        IterableUserDict.__init__(self)
        self.size_x = x
        self.size_y = y
        self.all_coord = set(itertools.product(range(x), range(y)))

    def add_layer(self, name, create_default_obj):
        layer = Layer(name, self)
        self[name] = layer
        layer.default_object = create_default_obj(layer=layer)
        return layer

    def constructor(self):
        return self.size_x, self.size_y

    @public.send_meth('setSize')
    def set_size(self, x, y):
        if 5 < x < 50:
            self.size_x = x
        if 5 < y < 50:
            self.size_y = y
        return self.size_x, self.size_y

    def subscribe(self, sub):
        for layer in self.values():
            sub.subscribe(layer)

    def unsubscribe(self, sub):
        for layer in self.values():
            sub.unsubscribe(layer)

@public.send_cls()
class Layer(objects.SendWeakDict):
    def __init__(self, name, gamemap):
        super(Layer, self).__init__()
        self.name = name
        self.gamemap = gamemap
        self.default_object = None

    def constructor(self):
        return self.name, self.default_object.indef

    def get_free_coord(self):
        free = self.gamemap.all_coord.difference(self.keys())
        try:
            return random.choice(tuple(free))
        except IndexError:
            return None

    def coord_handling(self, coord):
        return coord[0] % self.gamemap.size_x, \
               coord[1] % self.gamemap.size_y

    def __getitem__(self, coord):
        coord = self.coord_handling(coord)
        if coord in self:
            return super(Layer, self).__getitem__(coord)
        return self.default_object.create_tile(coord)

class NoSendTile(object):
    def __init__(self, coord, info=''):
        self.info = info
        self.coord = self.layer.coord_handling(coord)
        if self.coord in self.layer.__dict__:
            del self.layer[self.coord]

    def can_start(self):
        objs = self.iter_tiles()
        return all(obj.can_start for obj in objs)

    def iter_tiles(self):
        for layer in self.layer.gamemap.values():
            yield layer[self.coord].game_object

@public.send_cls(wrapper=False)
class Tile(NoSendTile):
    send_key = lambda self, _: self.coord
    send_once = 'indef',
    send_attrs = 'info',

    def __init__(self, coord, info=''):
        self.info = info
        self.coord = self.layer.coord_handling(coord)
        self.layer[self.coord] = self

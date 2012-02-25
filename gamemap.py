#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import itertools
from weakref import WeakValueDictionary
from collections import namedtuple

from sender import public, objects
from sender.base import WrapperUnique

@public.send_cls(wrapper=WrapperUnique)
class Gamemap(objects.SendDict):
    def __init__(self, x, y):
        objects.SendDict.__init__(self)
        self.Coord = get_coord(self, x, y)

    def add_layer(self, name, create_default_obj):
        layer = Layer(name, self.Coord)
        self.add(layer)
        layer.default_object = create_default_obj(layer=layer)
        return layer

    def init(self):
        return self.Coord.size_x, self.Coord.size_y

    def subscribe(self, sub):
        for layer in self.values():
            sub.subscribe(layer)

    def unsubscribe(self, sub):
        for layer in self.values():
            sub.unsubscribe(layer)

@public.send_cls()
class Layer(objects.SendWeakDict):
    send_attrs = 'name',

    def __init__(self, name, Coord):
        objects.SendWeakDict.__init__(self)
        self.name = name
        self.Coord = Coord
        self.default_object = None

    def init(self):
        return self.name, self.default_object.indef

    def add_mapobject(self, obj, coord, info=''):
        coord = self.Coord(coord)
        mapobject = MapObject(obj, coord, info)
        self.add(mapobject)
        return mapobject

    def get_free_coord(self):
        free = self.Coord.all_coord.difference(self.keys())
        try:
            return random.choice(tuple(free))
        except IndexError:
            return None

    def subscribe(self, sub):
        pass

    def unsubscribe(self, sub):
        pass

    def __getitem__(self, coord):
        coord = self.Coord(coord)
        if coord in self:
            return objects.SendWeakDict.__getitem__(self, coord)
        return MapObject(self.default_object, coord)

@public.send_cls(wrapper=False)
class MapObject(object):
    send_attrs = 'coord', 'indef', 'info'

    def __init__(self, obj, coord, info=''):
        self.obj = obj
        self.indef = obj.indef
        self.layer = obj.layer
        self.info = info
        self.coord = coord

    def can_start(self):
        objs = self.coord.iter_objs()
        return all(obj.can_start for obj in objs)

_Coord = namedtuple('Coord', ['x', 'y'])
def get_coord(gamemap, x, y):
    class Coord(_Coord):
        __slots__ = ()

        def __new__(cls, x, y=0):
            if isinstance(x, (tuple, list)):
                x, y = x
            x %= cls.size_x
            y %= cls.size_y

            return _Coord.__new__(Coord, x, y)

        def __sub__(self, o):
            return self.x - o[0], self.y - o[1]

        def __add__(self, o):
            return self.x + o[0], self.y + o[1]

        def get_obj(self, key):
            return self.gamemap[key][self].obj

        def iter_objs(self):
            for layer in self.gamemap.values():
                yield layer[self].obj

    Coord.gamemap = gamemap
    Coord.size_x = x
    Coord.size_y = y
    Coord.all_coord = set(itertools.product(range(x), range(y)))
    return Coord


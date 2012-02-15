#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import WeakValueDictionary
from collections import namedtuple

from sender import public, objects
from sender.base import WrapperUnique

_Coord = namedtuple('Coord', ['x', 'y'])
class Coord(_Coord):
    __slots__ = ()

    def __new__(cls, x, y=0):
        if isinstance(x, (tuple, list)):
            x, y = x
        return _Coord.__new__(Coord, x, y)

    def __sub__(self, o):
        return self.x - o[0], self.y - o[1]

    def __add__(self, o):
        return self.x + o[0], self.y + o[1]

@public.send_cls(wrapper=WrapperUnique)
class Gamemap(objects.SendDict):
    def __init__(self, x, y):
        objects.SendDict.__init__(self)
        self.x = x
        self.y = y

    def add_layer(self, name):
        layer = Layer(name, self)
        self.add(layer)
        return layer

    def init(self):
        return self.x, self.y

    def subscribe(self, sub):
        for layer in self.values():
            sub.subscribe(layer)

    def unsubscribe(self, sub):
        for layer in self.values():
            sub.unsubscribe(layer)

    def can_start(self, coord):
        if coord in self['base']:
            return False
        mapobj = self['ground'][coord].obj
        return getattr(mapobj, 'start_pos', False)

@public.send_cls()
class Layer(objects.SendWeakDict):
    send_attrs = 'name',

    def __init__(self, name, container):
        objects.SendWeakDict.__init__(self)
        self.name = name
        self.container = container

    def init(self):
        return self.name, self.default_object.obj.indef

    def set_default(self, default_object):
        self.default_object = MapObject(default_object, None)

    def get_real_coord(self, coord):
        return Coord(coord[0] % self.container.x,
                     coord[1] % self.container.y)

    def add_mapobject(self, obj, coord, info=''):
        coord = self.get_real_coord(coord)
        mapobject = MapObject(obj, coord, info)
        self.add(mapobject)
        return mapobject

    def subscribe(self, sub):
        pass

    def unsubscribe(self, sub):
        pass

    def __getitem__(self, coord):
        coord = self.get_real_coord(coord)
        if coord in self:
            return objects.SendWeakDict.__getitem__(self, coord)
        return self.default_object

@public.send_cls()
class MapObject(object):
    send_attrs = 'coord', 'indef', 'info'

    def __init__(self, obj, coord, info=''):
        self.obj = obj
        self.indef = obj.indef
        self.layer = obj.layer
        self.info = info
        self.coord = coord

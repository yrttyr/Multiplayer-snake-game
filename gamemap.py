#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import WeakValueDictionary
from collections import namedtuple

from sender import public
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
class Gamemap(dict):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def add_layer(self, name):
        layer = Layer(self)
        self[name] = layer
        return layer

    def get_layers_data(self):
        d = {}
        for name, layer in self.items():
            d[name] = layer.default_object.obj.indef
        return d

    def init(self):
        return self.x, self.y, self.get_layers_data()

    @public.send_meth('set_mapobject')
    def send_mapobject(self, obj_data):
        return obj_data

    def can_start(self, coord):
        if coord in self['base']:
            return False
        mapobj = self['ground'][coord].obj
        return getattr(mapobj, 'start_pos', False)

class Layer(WeakValueDictionary):
    def __init__(self, container):
        WeakValueDictionary.__init__(self)
        self.container = container

    def set_default(self, default_object):
        self.default_object = MapObject(None, default_object)

    def get_real_coord(self, coord):
        return Coord(coord[0] % self.container.x,
                     coord[1] % self.container.y)

    def changed(self, coord):
        obj = self[coord]
        self.container.send_mapobject((obj.obj.indef, obj.coord, obj.info))

    def del_(self, coord):
        obj = self.default_object
        self.container.send_mapobject((obj.obj.indef, coord, obj.info))

    def __setitem__(self, coord, value):
        coord = self.get_real_coord(coord)
        WeakValueDictionary.__setitem__(self, coord, value)
        obj = self[coord]
        self.container.send_mapobject((obj.obj.indef, obj.coord, obj.info))

    def __getitem__(self, coord):
        coord = self.get_real_coord(coord)
        return self.get(coord, self.default_object)

class MapObject(object):
    def __init__(self, coord, obj, info_val = ''):
        self.obj = obj
        self.layer = obj.layer
        self._info = info_val

        if coord:
            self.coord = self.layer.get_real_coord(coord)
            self.layer[coord] = self

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, value):
        if self._info != value:
            self._info = value
            self.layer.changed(self.coord)

    def __del__(self):
        self.layer.del_(self.coord)



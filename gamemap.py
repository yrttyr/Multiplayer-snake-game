#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import WeakValueDictionary
from collections import namedtuple

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

class Gamemap(dict):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def add_layer(self, name):
        self[name] = Layer(self)

    def changed(self):
        return any(layer.change for layer in self.values())

    def get_layers_data(self):
        d = {}
        for name, layer in self.items():
            d[name] = layer.default_object.obj.indef
        return d

    def get_changed_data(self):
        data = []
        for layer in self.values():
             data.extend(layer.get_change_coord())
             del layer.change[:]
        return data

    def clear_changed_data(self):
        for layer in self.values():
            del layer.change[:]

    def can_start(self, coord):
        if coord in self['base']:
            return False
        mapobj = self['ground'][coord].obj
        return getattr(mapobj, 'start_pos', False)

class Layer(WeakValueDictionary):
    def __init__(self, container):
        WeakValueDictionary.__init__(self)
        self.container = container
        self.change = []

    def set_default(self, default_object):
        self.default_object = MapObject(None, default_object)

    def __setitem__(self, key, value):
        key = Coord(key[0] % self.container.x,
                    key[1] % self.container.y)
        WeakValueDictionary.__setitem__(self, key, value)
        return key

    def __getitem__(self, key):
        key = key[0] % self.container.x, \
              key[1] % self.container.y
        return self.get(key, self.default_object)

    def get_change_coord(self):
        data = [[self.get(coord, self.default_object).obj.indef,
                coord, self.get(coord, self.default_object).info]
                for coord in set(self.change)]
        return data

class MapObject(object):
    def __init__(self, coord, obj, info_val = ''):
        self.obj = obj
        self._info = info_val

        if coord:
            self.coord = self.layer.__setitem__(coord, self)
            self.layer.change.append(self.coord)

    @property
    def layer(self):
        return self.obj.gamemap[self.obj.map_layer]

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, value):
        if self._info != value:
            self._info = value
            self.layer.change.append(self.coord)

    def __del__(self):
        self.layer.change.append(self.coord)



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

    #def __hash__(self):
    #   return hash((self.x, self.y))

    #def __eq__(self, other):
    #   return (self.x, self.y) == (other.x, other.y)

class GameMapContainer(dict):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __setitem__(self, key, value):
        super(GameMapContainer, self).__setitem__(key, value)
        value.x = self.x
        value.y = self.y

    def changed(self):
        return any(gamemap.change for gamemap in self.values())

    def get_layers_data(self):
        d = {}
        for name, gamemap in self.items():
            d[name] = gamemap.default_object.obj.indef
        return d

    def get_changed_data(self):
        data = []
        for gamemap in self.values():
             data.extend(gamemap.get_change_coord())
             del gamemap.change[:]
        return data

class GameMap(WeakValueDictionary):
    #slots
    def __init__(self):
        WeakValueDictionary.__init__(self)
        self.change = []

    def set_default(self, default_object):
        self.default_object = MapObject(None, default_object)

    #def __setitem__(self, key, value):
    #   WeakValueDictionary.__setitem__(self, key, value)

    def __getitem__(self, key):
        #if not isinstance(key, str):
        key = key[0] % self.x, key[1] % self.y
        return self.get(key, self.default_object)

    def get_change_coord(self):
        data = [[self.get(coord, self.default_object).obj.indef,
                coord, self.get(coord, self.default_object).info]
                for coord in set(self.change)]
        #del self.change[:]
        return data

class MapObject(object):
    #slots
    def __init__(self, coord, obj, info_val = ''):
        self.obj = obj
        self._info = info_val

        if coord:
            self.coord = Coord(coord[0] % self.layer.x,
                                coord[1] % self.layer.y)
            self.layer.change.append(self.coord)
            self.layer[self.coord] = self

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



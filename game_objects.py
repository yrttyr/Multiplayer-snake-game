#!/usr/bin/env python
# -*- coding: utf-8 -*-

from random import randint
from itertools import count

from gevent import sleep, spawn

class GameObject(object):
    can_start = False
    get_id = count().next
    map_layer = 'base'
    cls_drawdata = {'drawtype': 'image'}

    def __init__(self, layer, coord):
        self.indef = self.get_id()
        self.drawdata = {'indef': self.indef,
                        'map_layer': self.map_layer}
        self.drawdata.update(self.cls_drawdata)

        self.layer = layer
        self.pieces = list()
        self.create_object(coord)

    def coll(self, coll_obj, map_object):
        return True

    def create_object(self, coords):
        for coord in coords:
            mapobject = self.layer.add_mapobject(self, coord)
            self.pieces.append(mapobject)

    def get_drawdata(self):
        return self.drawdata

class EmptyObject(GameObject):
    can_start = True
    cls_drawdata = {'drawtype': 'empty'}

class Ground(GameObject):
    map_layer = 'ground'
    cls_drawdata = {'drawtype': 'image',
                    'image': 'ground'}

class Rabbit(GameObject):
    can_start = True
    cls_drawdata = {'drawtype': 'image',
                    'image': 'rabbit'}

    def __init__(self, layer, coord):
        super(Rabbit, self).__init__(layer, coord)
        self.speed = 10.0
        self.greenlet = spawn(self.step)

    def coll(self, coll_obj, map_object):
        self.pieces.remove(map_object)
        coll_obj.len += 5
        coll_obj.scores(2)
        return True

    def step(self):
        while True:
            free = self.layer.get_free_coord()
            if free is not None:
                mapobject = self.layer.add_mapobject(self, free)
                self.pieces.append(mapobject)
            sleep(self.speed)

class Wall(GameObject):
    cls_drawdata = {'drawtype': 'wall'}

    def __init__(self, layer, coord):
        super(Wall, self).__init__(layer, coord)

    def coll(self, coll_obj, map_object):
        coll_obj.len -= 1
        return False

class StartPosition(GameObject):
    can_start = True
    map_layer = 'ground'
    cls_drawdata = {'drawtype': 'image',
                    'image': 'start_position'}
    start_pos = True

class Snake(GameObject):
    alive = False
    cls_drawdata = {'drawtype': 'snake'}
    direct = (0, -1), (1, 0), (0, 1), (-1, 0)

    def __init__(self, layer, color, scores):
        self.rotation = 0
        super(Snake, self).__init__(layer, ())
        self.speed = 0.4
        self.drawdata['color'] = color
        self.scores = scores

    def start(self, coord):
        if not self.layer[coord].can_start():
            return
        self.alive = True
        self.len = 3
        info = str(self.rotation) + 'h'
        mapobject = self.layer.add_mapobject(self, coord, info)
        self.pieces.append(mapobject)
        self.greenlet = spawn(self.step)

    def kill(self):
        self.alive = False
        del self.pieces[:]
        if hasattr(self, 'greenlet'):
            self.greenlet.kill()

    def del_last(self):
        self.pieces.pop(0)
        self.pieces[0].info = self.pieces[0].info[1] + '_'

    def add_new(self, coord):
        info = '_' + str((self.rotation + 2) % 4)
        mapobject = self.layer.add_mapobject(self, coord, info)
        self.pieces.append(mapobject)

        if self.pieces[-2].info[1] == 'b' or self.pieces[-2].info[1] == 'h':
            self.pieces[-2].info = 'b' + str(self.rotation)
        else:
            self.pieces[-2].info = self.pieces[-2].info[1] + str(self.rotation)

    def test_coll(self, coord):
        map_object = self.layer[coord]
        return map_object.obj.coll(self, map_object)

    def coll(self, coll_obj, map_object):
        coll_obj.len -= 1
        coll_obj.scores(-1)
        return False

    def step(self):
        while True:
            if self.len < 2:
                self.kill()

            if self.len < len(self.pieces):
                self.del_last()

            coord = self.pieces[-1].coord + self.direct[self.rotation]
            if self.test_coll(coord):
                self.add_new(coord)
            sleep(self.speed)

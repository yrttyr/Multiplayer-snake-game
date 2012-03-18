#!/usr/bin/env python
# -*- coding: utf-8 -*-

from random import randint
from itertools import count

from gevent import sleep, spawn

from gamemap import Tile

class GameObject(object):
    can_start = False
    get_id = count().next
    map_layer = 'base'
    cls_drawdata = {'drawtype': 'image'}
    tile_class = Tile

    def __init__(self, layer, coord):
        self.indef = self.get_id()
        self.drawdata = {'indef': self.indef,
                        'map_layer': self.map_layer}
        self.drawdata.update(self.cls_drawdata)

        self.layer = layer
        self.tiles = list()
        self.create_tile = self._create_tile_generator()
        self.create_object(coord)

    def _create_tile_generator(self):
        return type('Tile_%d' % self.indef, (self.tile_class,), {
            'game_object': self,
            #'indef': self.indef,
            'layer': self.layer})

    def coll(self, coll_obj, tile):
        return True

    def create_object(self, coords):
        for coord in coords:
            self.tiles.append(self.create_tile(coord))

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

    def coll(self, coll_obj, tile):
        self.tiles.remove(tile)
        coll_obj.len += 5
        coll_obj.scores(2)
        return True

    def step(self):
        while True:
            free = self.layer.get_free_coord()
            if free is not None:
                self.tiles.append(self.create_tile(free))
            sleep(self.speed)

class Wall(GameObject):
    cls_drawdata = {'drawtype': 'wall'}

    def __init__(self, layer, coord):
        super(Wall, self).__init__(layer, coord)

    def coll(self, coll_obj, tile):
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
        self.tiles.append(self.create_tile(coord, info))
        self.greenlet = spawn(self.step)

    def kill(self):
        self.alive = False
        del self.tiles[:]
        if hasattr(self, 'greenlet'):
            self.greenlet.kill()

    def del_last(self):
        self.tiles.pop(0)
        self.tiles[0].info = self.tiles[0].info[1] + '_'

    def add_new(self, coord):
        info = '_' + str((self.rotation + 2) % 4)
        self.tiles.append(self.create_tile(coord, info))

        if self.tiles[-2].info[1] == 'b' or self.tiles[-2].info[1] == 'h':
            self.tiles[-2].info = 'b' + str(self.rotation)
        else:
            self.tiles[-2].info = self.tiles[-2].info[1] + str(self.rotation)

    def test_coll(self, coord):
        tile = self.layer[coord]
        return tile.game_object.coll(self, tile)

    def coll(self, coll_obj, tile):
        coll_obj.len -= 1
        coll_obj.scores(-1)
        return False

    def step(self):
        while True:
            if self.len < 2:
                self.kill()

            if self.len < len(self.tiles):
                self.del_last()

            old = self.tiles[-1].coord
            dc = self.direct[self.rotation]
            coord = old[0] + dc[0], old[1] + dc[1]
            if self.test_coll(coord):
                self.add_new(coord)
            sleep(self.speed)

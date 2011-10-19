#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gevent import sleep, spawn
from random import randint
from gamemap import MapObject, Coord

class GameObject(object):
    def __init__(self, indef,  gamemap, coord, drawtype='image'):
        self.gamemap = gamemap
        self.pieces = list()
        self.create_object(coord)
        self.indef = indef
        self.drawdata = {'indef': self.indef,
                        'drawtype': drawtype,
                        'map_layer': self.map_layer}

    def coll(self, coll_obj, map_object):
        return True

    def create_object(self, coord):
        for val in coord:
            self.pieces.append(MapObject(val, self, self.gamemap[self.map_layer]))

    def get_coord(self):
        return self.indef, [(obj.coord, obj.info)
                for obj in self.pieces]

    def get_drawdata(self):
        return self.drawdata

class EmptyObject(GameObject):
    def __init__(self, indef, gamemap, coord):
        self.map_layer = 'base'
        super(EmptyObject, self).__init__(indef, gamemap, (), 'empty')

    def get_coord(self):
        return self.indef, []

class Ground(GameObject):
    def __init__(self, indef, gamemap, coord):
        self.map_layer = 'ground'
        super(Ground, self).__init__(indef, gamemap, ())
        self.drawdata['image'] = 'empty'

    def get_coord(self):
        return self.indef, []

class Rabbit(GameObject):
    def __init__(self, indef, gamemap, coord):
        self.map_layer = 'base'
        super(Rabbit, self).__init__(indef, gamemap, coord)
        self.drawdata['image'] = 'rabbit'
        self.speed = 10.0
        self.greenlet = spawn(self.step)

    def coll(self, coll_obj, map_object):
        self.pieces.remove(map_object)
        coll_obj.len += 5
        return True

    def step(self):
        while True:
            while True:
                coord = randint(0, self.gamemap[self.map_layer].x), randint(0, self.gamemap[self.map_layer].y)
                if isinstance(self.gamemap[self.map_layer][coord].obj, EmptyObject):
                    break
            self.pieces.append(MapObject(coord, self, self.gamemap[self.map_layer], ''))

            sleep(self.speed)

class Wall(GameObject):
    def __init__(self, indef, gamemap, coord):
        self.map_layer = 'base'
        super(Wall, self).__init__(indef, gamemap, coord, 'wall')

    def coll(self, coll_obj, map_object):
        coll_obj.len -= 1
        return False

class StartPosition(GameObject):
    def __init__(self, indef, gamemap, coord):
        self.map_layer = 'ground'
        super(StartPosition, self).__init__(indef, gamemap, coord)
        self.start_pos = True
        self.drawdata['image'] = 'start_position'

    #def coll(self, coll_obj, map_object):
    #   coll_obj.len -= 1
    #   return False

class Snake(GameObject):
    direct = (0, -1), (1, 0), (0, 1), (-1, 0)
    color = (255, 0, 0), (0, 255, 0), (0, 0, 255);
    getColor = iter(color).next
    def __init__(self, indef, gamemap, coord, rotation):
        self.rotation = rotation
        self.map_layer = 'base'
        super(Snake, self).__init__(indef, gamemap, coord, 'snake')
        self.len = 3
        self.speed = 0.4
        self.drawdata['color'] = self.getColor()
        self.greenlet = spawn(self.step)

    def create_object(self, coord):
        info = str(self.rotation) + '_'
        self.pieces.append(MapObject(coord[0], self, self.gamemap[self.map_layer], info))

    def step(self):
        while True:
            if self.len < 2:
                self.dead()

            if self.len < len(self.pieces):
                self.del_last()

            coord = self.pieces[-1].coord + self.direct[self.rotation]
            if self.test_coll(coord):
                self.add_new(coord)

            sleep(self.speed)

    def dead(self):
        print 'snake dead'
        self.greenlet.kill()

    def del_last(self):
        self.pieces.pop(0)
        self.pieces[0].info = self.pieces[0].info[1] + '_'

    def add_new(self, coord):
        info = '_' + str((self.rotation + 2) % 4)
        self.pieces.append(MapObject(coord, self, self.gamemap[self.map_layer], info))
        self.pieces[-2].info = self.pieces[-2].info[1] + str(self.rotation)

    def test_coll(self, coord):
        map_object = self.gamemap[self.map_layer][coord]
        return map_object.obj.coll(self, map_object)

    def coll(self, coll_obj, map_object):
        coll_obj.len -= 1
        return False

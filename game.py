#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from hashlib import md5

from gevent import sleep, spawn
from sender import sender

from gamemap import GameMap, GameMapContainer
import game_objects

@sender.send_cls(singleton=True)
class GamesList(list):
    call_with_conn = 'send_all_games',

    def __init__(self):
        self.change = []
        self.greenlet = spawn(self.step)

    def add_map(self):
        map_ = MapEditor(self)
        self.append(map_)
        return map_

    def add_game(self, key):
        game = Game(self, key)
        self.append(game)
        self.change.append(game)
        return game

    @sender.send_meth('gamelist')
    def send_all_games(self):
        return [(id(game), game.gamemap.x, game.gamemap.y)
                for game in self]

    @sender.send_meth('gamelist')
    def send_change_games(self):
        return [(id(game), game.gamemap.x, game.gamemap.y)
                for game in self.change]

    def step(self):
        while True:
            if self.change:
                self.send_change_games()
                del self.change[:]
            sleep(0.04)

games_list = GamesList()

@sender.send_cls(singleton=True)
class MapsList(list):
    call_with_conn = 'send_all_games',

    def __init__(self):
        files = os.listdir('maps/')
        files = [f for f in files if f[0] != '.']
        self.extend(files)

    @sender.send_meth('mapslist')
    def send_all_games(self):
        return [map_name for map_name in self]

maps_list = MapsList()

@sender.send_cls()
class AbstractGame(object):
    def __init__(self, cont):
        self.cont = cont
        self.objects = []
        self.new_objects = []
        self.map_edit = False

        def getId():
            a = 0
            while True:
                yield a
                a += 1
        self.get_objectId = getId().next

    def load_map(self, name):
        with open('maps/' + name) as f:
            data = json.load(f)

        self.gamemap = GameMapContainer(data['SizeX'], data['SizeY'])

        empty_obj = self.add_object('EmptyObject')
        ground_obj = self.add_object('Ground')
        self.gamemap['base'] = GameMap(empty_obj)
        self.gamemap['ground'] = GameMap(ground_obj)

        objects = data['objects']
        if 'Wall' in objects:
            self.add_object('Wall', objects['Wall'])
        if 'StartPosition' in objects:
            self.add_object('StartPosition', objects['StartPosition'])

    def add_object(self, name, coord=(), *arg, **kwarg):
        obj_class = getattr(game_objects, name)
        obj = obj_class(self.get_objectId(), self.gamemap,
                        coord, *arg, **kwarg)
        self.objects.append(obj)
        self.new_objects.append(obj)
        return obj

    @sender.send_meth('gameinfo')
    def send_gameinfo(self):
        return self.gamemap.x, self.gamemap.y, self.map_edit

    @sender.send_meth('allcoord')
    def send_all_coord(self):
        return [obj.get_coord() for obj in self.objects]

    @sender.send_meth('coord')
    def send_change_coord(self):
        return self.gamemap.get_changed_data()

    @sender.send_meth('drawdata')
    def send_all_drawdata(self):
        return [obj.get_drawdata() for obj in self.objects]

    @sender.send_meth('drawdata')
    def send_new_drawdata(self):
        return [obj.get_drawdata() for obj in self.new_objects]

@sender.send_cls()
class Game(AbstractGame):
    call_with_conn = 'send_gameinfo', 'send_all_drawdata', 'send_all_coord'

    def __init__(self, cont, map_key):
        super(Game, self).__init__(cont)

        self.load_map(maps_list[map_key])
        rabbit = game_objects.Rabbit(self.get_objectId(), self.gamemap, ())
        self.objects.append(rabbit)
        self.greenlet = spawn(self.step)

    def add_player(self, coord, direct):
        return self.add_object('Snake', (coord,), direct)

    def step(self):
        while True:
            if self.gamemap.changed():
                self.send_new_drawdata()
                self.send_change_coord()
                del self.new_objects[:]
            sleep(0.04)

@sender.send_cls('Game')
class MapEditor(AbstractGame):
    call_with_conn = 'send_gameinfo', 'send_all_drawdata', 'send_all_coord'

    def __init__(self, cont, map_key=None):
        super(MapEditor, self).__init__(cont)
        self.map_edit = True
        if map_key is None:
            self.load_map('.empty')

    @sender.recv_meth()
    def save_map(self, sub, data):
        map_dict = {}
        map_dict['SizeX'] = data['SizeX'];
        map_dict['SizeY'] = data['SizeY'];
        map_dict['objects'] = {};
        for obj in self.objects:
            map_dict['objects'][type(obj).__name__] = [
                coord for indef, coord in data['objects']
                if obj.indef == indef
            ]

        name = md5(str(map_dict)).hexdigest()
        with open('maps/' + name, 'w') as f:
            data = json.dump(map_dict, f)

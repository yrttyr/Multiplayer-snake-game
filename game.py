#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from hashlib import md5
from weakref import WeakSet

from gevent import sleep, spawn
from sender import sender

from gamemap import GameMapContainer
import game_objects

@sender.send_cls(singleton=True)
class GamesList(list):
    call_with_conn = 'send_all_games',

    def __init__(self):
        self.change = []
        self.greenlet = spawn(self.step)

    @sender.recv_meth()
    def create_map(self, sub):
        map_ = MapEditor(self)
        self.append(map_)
        sub.subscribe(map_)

    @sender.recv_meth()
    def create_game(self, sub, key):
        game = Game(self, key)
        self.append(game)
        self.change.append(game)
        self.connect_game(sub, game)
        sub.subscribe(game)
        sub.get_sendobj('Player').clear(game)

    @sender.recv_meth()
    def connect_game(self, sub, game_id):
        sub.subscribe(game_id)
        game = sub.get_sendobj('Game')
        sub.get_sendobj('Player').clear(game)

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
        self.new_objects = WeakSet()
        self.map_edit = False

    def load_map(self, name):
        with open('maps/' + name) as f:
            data = json.load(f)

        self.gamemap = GameMapContainer(data['SizeX'], data['SizeY'])
        for layer_name in data['layers'].keys():
            self.gamemap.add_layer(layer_name)

        for name, coord in data['objects']:
            self.add_object(name, coord)

        for layer_name, obj_id in data['layers'].items():
            self.gamemap[layer_name].set_default(self.objects[obj_id])

    def add_object(self, name, coord=(), *arg, **kwarg):
        obj_class = getattr(game_objects, name)
        obj = obj_class(self.gamemap, coord, *arg, **kwarg)
        self.objects.append(obj)
        self.new_objects.add(obj)
        return obj

    @sender.send_meth('gameinfo')
    def send_gameinfo(self):
        return self.gamemap.x, self.gamemap.y, \
               self.gamemap.get_layers_data(), self.map_edit

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

        self.max_snake = 3
        self.snake_count = 0
        self.load_map(maps_list[map_key])
        self.snake_color = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
                            (255, 255, 0), (255, 0, 255), (0, 255, 255)]
        self.add_object('Rabbit')
        self.greenlet = spawn(self.step)

    def add_snake(self, coord, direct):
        if self.snake_count >= self.max_snake:
            return None
        self.snake_count += 1
        return self.add_object('Snake', coord, direct,
                               self.snake_color.pop())

    def remove_snake(self, snake):
        self.snake_count -= 1
        self.snake_color.append(snake.drawdata['color'])
        snake.kill()
        self.objects.remove(snake)

    def step(self):
        while True:
            if self.gamemap.changed():
                self.send_new_drawdata()
                self.send_change_coord()
                self.new_objects.clear()
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
        map_dict['SizeX'] = data['SizeX']
        map_dict['SizeY'] = data['SizeY']

        map_dict['layers'] = {}
        map_dict['objects'] = []
        for obj in self.objects:
            map_dict['objects'].append(
                (type(obj).__name__,
                [coord for indef, coord in data['objects']
                if obj.indef == indef])
            )
            for name, layer in self.gamemap.items():
                if layer.default_object.obj is obj:
                    map_dict['layers'][name] = len(map_dict['objects']) - 1

        name = md5(str(map_dict)).hexdigest()
        with open('maps/' + name, 'w') as f:
            data = json.dump(map_dict, f)

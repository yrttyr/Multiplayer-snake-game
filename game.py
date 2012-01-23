#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from hashlib import md5
from weakref import WeakSet

from gevent import sleep, spawn
import sender.objects
from sender import public
from sender.base import WrapperSingleton, WrapperUnique

from gamemap import GameMapContainer
import player
import game_objects

class MaxplayerError(Exception):
    def __str__(self):
        return 'Достигнуто максимальное количество игроков'

@public.send_cls(wrapper=WrapperSingleton)
class MapsList(set):
    def __init__(self):
        files = os.listdir('maps/')
        files = [f for f in files if not f.startswith('.')]
        self.update(files)

    def init(self):
        return ()

    def subscribe(self, sub):
        self.send_all_games(to=sub)

    @public.send_meth('addList')
    def send_all_games(self):
        return [map_name for map_name in self],

    def __del__(self):
        print 'ML del', self, id(self)

maps_list = MapsList()

@public.send_cls(wrapper=WrapperSingleton)
class GamesList(sender.objects.SendList):

    @public.recv_meth()
    def create_map(self, sub):
        map_ = MapEditor(self)
        self.append(map_)
        sub.subscribe(map_)
        sub['Player'].setdata(map_)

    @public.recv_meth()
    def create_game(self, sub, key):
        game = Game(self, key)
        self.connect_game(sub, game)

    @public.recv_meth()
    def connect_game(self, sub, game_id):
        sub.subscribe(game_id)
        game = sub['Game']
        sub['Player'].setdata(game)

        #for s in sub['Game']:
        #    scores = s.get_obj('Player').scores
        #    if scores:
        #        scores.send_score(to=sub)

@public.send_cls()
class AbstractGame(object):
    def __init__(self, cont):
        self.cont = cont
        self.objects = []
        self._status = None

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        self.send_status()

    def load_map(self, name):
        if name not in maps_list:
            raise 'Unknown map'

        with open('maps/' + name) as f:
            data = json.load(f)

        self.gamemap = GameMapContainer(data['SizeX'], data['SizeY'])
        for layer_name in data['layers'].keys():
            self.gamemap.add_layer(layer_name)

        for name, coord in data['objects']:
            self.add_object(name, coord)

        for layer_name, obj_id in data['layers'].items():
            self.gamemap[layer_name].set_default(self.objects[obj_id])

        self.gamemap.clear_changed_data()

    def add_object(self, name, coord=(), *arg, **kwarg):
        obj_class = getattr(game_objects, name)
        obj = obj_class(self.gamemap, coord, *arg, **kwarg)
        self.objects.append(obj)
        self.send_drawdata(obj)
        return obj

    @public.send_meth('game_status')
    def send_status(self):
        return self.status

    @public.send_meth('mapdata')
    def send_mapdata(self):
        return self.gamemap.x, self.gamemap.y, \
               self.gamemap.get_layers_data()

    @public.send_meth('allcoord')
    def send_all_coord(self):
        return [obj.get_coord() for obj in self.objects]

    @public.send_meth('coord')
    def send_change_coord(self):
        return self.gamemap.get_changed_data()

    @public.send_meth('drawdata')
    def send_all_drawdata(self):
        return [obj.get_drawdata() for obj in self.objects]

    @public.send_meth('drawdata')
    def send_drawdata(self, obj):
        return [obj.get_drawdata()]

@public.send_cls(wrapper=WrapperUnique)
class Game(AbstractGame):
    games_list = GamesList(('snake_count', ))
    call_with_conn = 'send_mapdata', 'send_all_drawdata', \
                     'send_all_coord', 'send_status'

    def __init__(self, cont, map_name):
        super(Game, self).__init__(cont)

        self.max_snake = 3
        self.snake_count = 0
        self.load_map(map_name)
        self.snake_color = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
                            (255, 255, 0), (255, 0, 255), (0, 255, 255)]
        self.add_object('Rabbit')
        self.status = 'play'

        self.greenlet = spawn(self.step)

    def add_snake(self, coord, direct):
        if self.snake_count >= self.max_snake:
            raise MaxplayerError
        self.snake_count += 1
        scores = player.Scores()
        snake = self.add_object('Snake', coord, direct,
                               self.snake_color.pop(), scores)
        scores.setdata(self, snake.indef)
        return snake, scores

    def remove_snake(self, snake):
        self.snake_count -= 1
        self.snake_color.append(snake.drawdata['color'])
        snake.kill()
        self.objects.remove(snake)

    def step(self):
        while True:
            if self.gamemap.changed():
                self.send_change_coord()
            sleep(0.04)

@public.send_cls(wrapper=WrapperUnique) #'Game')
class MapEditor(AbstractGame):
    call_with_conn = 'send_mapdata', 'send_all_drawdata', \
                     'send_all_coord', 'send_status'

    def __init__(self, cont, map_key=None):
        super(MapEditor, self).__init__(cont)

        if map_key is None:
            self.load_map('.empty')
        self.status = 'map_editor'

    @public.recv_meth()
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

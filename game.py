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

from gamemap import Gamemap
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
        sub.subscribe(map_)
        sub['Player'].setdata(map_)

    @public.recv_meth()
    def create_game(self, sub, map_key):
        game = Game(self, map_key)
        self.subscribe_to(sub, game)

@public.send_cls(wrapper=WrapperSingleton)
class PlayersList(sender.objects.SendList):
    pass

@public.send_cls()
class AbstractGame(object):
    def __init__(self, cont):
        self.cont = cont
        self.objects = []

    def load_map(self, name):
        if name not in maps_list:
            raise 'Unknown map'

        with open('maps/' + name) as f:
            data = json.load(f)

        self.gamemap = Gamemap(data['SizeX'], data['SizeY'])

        for layer_name, default_tile in data['layers'].items():
            layer = self.gamemap.add_layer(layer_name)
            default_obj = self.add_object(default_tile, layer=layer)
            layer.set_default(default_obj)

        for name, coord in data['objects']:
            self.add_object(name, coord)

    def add_object(self, name, coord=(), *arg, **kwarg):
        cls = getattr(game_objects, name)
        layer = kwarg.pop('layer', None)
        if layer is None:
            layer = self.gamemap[cls.map_layer]
        obj = cls(layer, coord, *arg, **kwarg)
        self.objects.append(obj)
        self.send_drawdata(obj)
        return obj

    @public.send_meth('setAllListCoord')
    def send_all_coord(self):
        return [obj.get_coord() for obj in self.objects],

    @public.send_meth('setListDrawdata')
    def send_all_drawdata(self):
        return [obj.get_drawdata() for obj in self.objects],

    @public.send_meth('setDrawdata')
    def send_drawdata(self, obj):
        return [obj.get_drawdata()]

@public.send_cls(wrapper=WrapperUnique)
class Game(AbstractGame):
    send_attrs = 'snake_count',

    def __init__(self, cont, map_name):
        super(Game, self).__init__(cont)

        self.players = PlayersList()
        self.max_snake = 3
        self.snake_count = 0
        self.load_map(map_name)
        self.snake_color = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
                            (255, 255, 0), (255, 0, 255), (0, 255, 255)]
        self.add_object('Rabbit')

    def subscribe(self, sub):
        if self.snake_count >= self.max_snake:
            raise MaxplayerError

        sub.subscribe(self.gamemap)

        self.snake_count += 1

        player = sub['Player']
        self.players.add(player)
        snake = self.add_object('Snake',
            self.snake_color.pop(), player.scores_contr)
        player.new_game(snake)

        sub.subscribe(self.players)
        self.send_all_drawdata(to=sub)
        self.send_all_coord(to=sub)

    def unsubscribe(self, sub):
        self.snake_count -= 1

        player = sub['Player']
        self.players.remove(player)
        snake = player.snake
        self.objects.remove(snake)
        self.snake_color.append(snake.drawdata['color'])
        player.end_game()

        sub.unsubscribe(self.players)
        sub.unsubscribe(self.gamemap)

gameslist = GamesList(Game)

@public.send_cls(wrapper=WrapperUnique)
class MapEditor(AbstractGame):
    def __init__(self, cont, map_key=None):
        super(MapEditor, self).__init__(cont)

        if map_key is None:
            self.load_map('.empty')

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

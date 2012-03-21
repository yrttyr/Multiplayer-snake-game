#!/usr/bin/env python
# -*- coding: utf-8 -*-

import UserDict
import json
import os
import re
from functools import partial
from collections import defaultdict

from gevent import sleep
from sender import objects
from sender import public
from sender.base import WrapperSingleton, WrapperUnique

from gamemap import Gamemap
import player
import game_objects

class MaxplayerError(Exception):
    def __str__(self):
        return 'Достигнуто максимальное количество игроков'

@public.send_cls(wrapper=WrapperSingleton)
class MapsList(object, UserDict.IterableUserDict):
    def __init__(self):
        self.data = {}
        self.names = []
        files = os.listdir('maps/')
        for filename in files:
            with open('maps/' + filename) as file:
                data = json.load(file)
                self.data[filename] = data
                if data['name']:
                    self.names.append(data['name'])

    def subscribe(self, sub):
        self.send_all_games(to=sub)

    @public.send_meth('addList')
    def send_all_games(self):
        return self.names,

    def __getitem__(self, name):
        if name == '':
            name = '.empty'
        else:
            name = re.sub('\W', '', name)
        return super(MapsList, self).__getitem__(name)

    def __setitem__(self, name, data):
        name = re.sub('\W', '', name)
        if not 0 != len(name) < 20:
            raise
        with open('maps/' + name, 'w') as f:
            json.dump(data, f, indent=4)
        super(MapsList, self).__setitem__(name, data)

maps_list = MapsList()

@public.send_cls(wrapper=WrapperSingleton)
class GamesList(objects.SendList):

    @public.recv_meth()
    def create_map(self, sub, map_name=''):
        map_editor = MapEditor(self, map_name)
        sub.subscribe(map_editor)

    @public.recv_meth()
    def create_game(self, sub, map_name):
        game = Game(self, map_name)
        sub.subscribe(game)

    @public.recv_meth()
    def subscribe_to(self, sub, key):
        sub.subscribe(key)

    @public.recv_meth()
    def unsubscribe_to(self, sub, key):
        sub.unsubscribe(key)

@public.send_cls()
class PlayersList(objects.SendList):
    pass

@public.send_cls()
class AbstractGame(object):
    def __init__(self, cont):
        self.cont = cont
        self.objects = []

    def load_map(self, name):
        data = maps_list[name]
        self.gamemap = Gamemap(data['SizeX'], data['SizeY'])

        for layer_name, default_tile in data['layers'].items():
            create_default_obj = partial(self.add_object, default_tile)
            layer = self.gamemap.add_layer(layer_name, create_default_obj)

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

    @public.send_meth('setListDrawdata')
    def send_all_drawdata(self):
        return [obj.get_drawdata() for obj in self.objects],

    @public.send_meth('setDrawdata')
    def send_drawdata(self, obj):
        return [obj.get_drawdata()]

@public.send_cls(wrapper=WrapperUnique)
class Game(AbstractGame):
    send_attrs = 'snake_count',

    def __init__(self, container, map_name):
        super(Game, self).__init__(container)

        self.players = PlayersList()
        self.max_snake = 3
        self.snake_count = 0
        self.load_map(map_name)
        self.snake_color = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
                            (255, 255, 0), (255, 0, 255), (0, 255, 255)]
        self.add_object('Rabbit')

    def subscribe(self, sub):
        sub.pop('MapEditor', None)
        if self.snake_count >= self.max_snake:
            raise MaxplayerError
        self.snake_count += 1

        pl = sub['Player']
        self.players.add(pl)
        snake = partial(self.add_object, 'Snake',
                        self.snake_color.pop())
        pl.wrapper = partial(player.GameWrapper, snake)

        sub.subscribe(self.gamemap)
        sub.subscribe(self.players)
        self.send_all_drawdata(to=sub)

    def unsubscribe(self, sub):
        self.snake_count -= 1

        pl = sub['Player']
        self.players.remove(pl)
        snake = pl.wrapper.snake
        self.objects.remove(snake)
        self.snake_color.append(snake.drawdata['color'])
        del pl.wrapper

        sub.unsubscribe(self.gamemap)
        sub.unsubscribe(self.players)

        if self.snake_count == 0:
            gameslist.remove(self)

gameslist = GamesList(Game)

@public.send_cls(wrapper=WrapperUnique)
class MapEditor(AbstractGame):
    def __init__(self, cont, map_name=''):
        super(MapEditor, self).__init__(cont)
        self.name = map_name
        self.load_map(map_name)

    def constructor(self):
        return self.name,

    @public.recv_meth()
    def save_map(self, sub, name):
        map_dict = {}
        map_dict['name'] = name
        sizeX = map_dict['SizeX'] = self.gamemap.size_x
        sizeY = map_dict['SizeY'] = self.gamemap.size_y

        map_dict['layers'] = {}
        map_dict['objects'] = []
        for obj in self.objects:
            map_dict['objects'].append(
                (type(obj).__name__,
                [piece.coord for piece in obj.pieces
                 if 0 <= piece.coord[0] <= sizeX and
                    0 <= piece.coord[1] <= sizeY])
            )
            for l_name, layer in self.gamemap.items():
                default_tile = type(layer.default_object).__name__
                map_dict['layers'][l_name] = default_tile
        maps_list[name] = map_dict

    @public.recv_meth()
    def exit(self, sub):
        del sub['MapEditor']

    def subscribe(self, sub):
        sub.pop('Game', None)
        pl = sub['Player']
        pl.wrapper = partial(player.MapEditorWrapper, self)
        sub.subscribe(self.gamemap)
        self.send_all_drawdata(to=sub)
        self.send_tiles(to=sub)

    def unsubscribe(self, sub):
        del sub['Player'].wrapper
        sub.unsubscribe(self.gamemap)

    @public.send_meth('setTiles')
    def send_tiles(self):
        tiles = defaultdict(list)
        for obj in self.objects:
            tiles[obj.map_layer].append(obj.indef)
        return tiles,

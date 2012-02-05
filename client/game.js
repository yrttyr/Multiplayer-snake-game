var Game, Gamemap, GamemapContainer, GamesList, MapsList, Player, PlayersList, needDraw_fill, update,
  __indexOf = Array.prototype.indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

needDraw_fill = function(X, Y) {
  var x, y, _results;
  _results = [];
  for (x = 0; 0 <= X ? x <= X : x >= X; 0 <= X ? x++ : x--) {
    _results.push((function() {
      var _results2;
      _results2 = [];
      for (y = 0; 0 <= Y ? y <= Y : y >= Y; 0 <= Y ? y++ : y--) {
        _results2.push(gamemap_cont.needDraw.push([x, y]));
      }
      return _results2;
    })());
  }
  return _results;
};

GamemapContainer = (function() {

  function GamemapContainer(layers) {
    var layer, name;
    this.canvas = document.getElementById('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.needDraw = [];
    window.gamemap = {};
    for (name in layers) {
      layer = layers[name];
      gamemap[name] = new Gamemap(layer);
    }
  }

  GamemapContainer.prototype.setSize = function(SizeX, SizeY) {
    this.SizeX = SizeX;
    this.SizeY = SizeY;
    return this.refreshCanvas();
  };

  GamemapContainer.prototype.setSizeX = function(x) {
    this.SizeX = x || parseInt(document.getElementById('Size_X').value);
    this.refreshCanvas();
    return needDraw_fill(gamemap_cont.SizeX, gamemap_cont.SizeY);
  };

  GamemapContainer.prototype.setSizeY = function(y) {
    this.SizeY = y || parseInt(document.getElementById('Size_Y').value);
    this.refreshCanvas();
    return needDraw_fill(gamemap_cont.SizeX, gamemap_cont.SizeY);
  };

  GamemapContainer.prototype.refreshCanvas = function() {
    document.getElementById('Size_X').value = this.SizeX;
    document.getElementById('Size_Y').value = this.SizeY;
    this.canvas.width = this.SizeX * CELLSIZE;
    this.canvas.height = this.SizeY * CELLSIZE;
    return this.canvas.style.display = 'block';
  };

  GamemapContainer.prototype.addObject = function(indef, coord, info) {
    var gamemap_name;
    gamemap_name = game.objects[indef].gamemap;
    return gamemap[gamemap_name].set(coord, indef, info);
  };

  return GamemapContainer;

})();

Gamemap = (function() {

  function Gamemap(default_obj_id) {
    this.default_obj_id = default_obj_id;
    this.dict = {};
  }

  Gamemap.prototype.set = function(k, x, type) {
    this.dict[k] = {
      'indef': x,
      'type': type || ''
    };
    return gamemap_cont.needDraw.push(k);
  };

  Gamemap.prototype.setType = function(k, x) {
    if (__indexOf.call(this.dict, k) >= 0) {
      this.dict[k].type = x;
      return gamemap_cont.needDraw.push(k);
    } else {
      return console.error('Cell empty', k);
    }
  };

  Gamemap.prototype.get = function(k) {
    return this.dict[k] || {
      'indef': this.default_obj_id,
      'type': ''
    };
  };

  Gamemap.prototype.getType = function(k) {
    if (__indexOf.call(this.dict, k) >= 0) return this.dict[k].type;
    return '';
  };

  Gamemap.prototype.getListIdAndCoord = function() {
    var coord, data, indef, key, value, _ref;
    data = [];
    _ref = this.dict;
    for (key in _ref) {
      value = _ref[key];
      indef = value.indef;
      if (indef === 0 || indef === 1) continue;
      coord = key.split(',');
      coord = [parseInt(coord[0]), parseInt(coord[1])];
      if (coord[0] < 0 || coord[0] >= game.SizeX || coord[1] < 0 || coord[1] >= game.SizeY) {
        continue;
      }
      data.push([indef, coord]);
    }
    return data;
  };

  return Gamemap;

})();

GamesList = (function() {

  function GamesList() {
    var button, title,
      _this = this;
    this.div = document.getElementById('games');
    this.maplist = document.getElementById('mapslist');
    button = document.createElement('input');
    button.type = 'button';
    button.value = 'Создать игру';
    button.onclick = function() {
      if (_this.maplist.value !== '') {
        return connect.sendData([_this, 'create_game', _this.maplist.value]);
      }
    };
    this.div.appendChild(button);
    button = document.createElement('input');
    button.type = 'button';
    button.value = 'Редактор карт';
    button.onclick = function() {
      if (_this.input.value !== '') {
        connect.sendData([_this, 'create_map', _this.input.value]);
        return _this.input.value = '';
      }
    };
    this.div.appendChild(button);
    title = document.createElement('div');
    title.innerHTML = 'Список игр';
    this.div.appendChild(title);
  }

  GamesList.prototype.set = function(indef, data) {
    var button, el,
      _this = this;
    el = document.getElementById(indef);
    if (!el) {
      el = document.createElement('div');
      el.setAttribute('id', indef);
      this.div.appendChild(el);
    }
    button = document.createElement('input');
    button.type = 'button';
    button.value = indef;
    button.onclick = function() {
      return connect.sendData([_this, 'subscribe_to', indef]);
    };
    return el.appendChild(button);
  };

  return GamesList;

})();

MapsList = (function() {

  function MapsList() {
    this.div = document.getElementById('mapslist');
  }

  MapsList.prototype.addList = function(list) {
    var el, _i, _len, _results;
    _results = [];
    for (_i = 0, _len = list.length; _i < _len; _i++) {
      el = list[_i];
      _results.push(this.add(el));
    }
    return _results;
  };

  MapsList.prototype.add = function(mapname) {
    var len;
    len = this.div.options.length;
    return this.div.options[len] = new Option(mapname, mapname);
  };

  return MapsList;

})();

PlayersList = (function() {

  function PlayersList() {
    this.div = document.getElementById('scoreslist');
  }

  PlayersList.prototype.set = function(indef, data) {
    var el;
    el = document.getElementById(indef);
    if (!el) {
      el = document.createElement('div');
      el.setAttribute('id', indef);
      this.div.appendChild(el);
    }
    return el.innerHTML = data;
  };

  return PlayersList;

})();

Game = (function() {

  function Game() {
    window.game = this;
    this.canvas = document.getElementById('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.objects = {};
    document.getElementById('etitorTools').style.display = 'none';
    document.getElementById('games').style.display = 'block';
  }

  Game.prototype.drawAll = function() {
    var base, base_obj, coord, ground, ground_obj, key, _ref, _results;
    _ref = gamemap_cont.needDraw;
    _results = [];
    for (key in _ref) {
      coord = _ref[key];
      ground = gamemap['ground'].get(coord);
      base = gamemap['base'].get(coord);
      ground_obj = this.objects[ground.indef];
      ground_obj.draw(coord[0], coord[1], ground.type);
      base_obj = this.objects[base.indef];
      base_obj.draw(coord[0], coord[1], base.type);
      _results.push(gamemap_cont.needDraw.splice(key, 1));
    }
    return _results;
  };

  Game.prototype.setMapdata = function(x, y, layer) {
    window.gamemap_cont = new GamemapContainer(layer);
    gamemap_cont.setSize(x, y);
    return needDraw_fill(x, y);
  };

  Game.prototype.setListDrawdata = function(list) {
    var el, _i, _len, _results;
    _results = [];
    for (_i = 0, _len = list.length; _i < _len; _i++) {
      el = list[_i];
      _results.push(this.setDrawdata(el));
    }
    return _results;
  };

  Game.prototype.setDrawdata = function(data) {
    this.objects[data['indef']] = new objectTypes[data['drawtype']](data);
    return this.objects[data['indef']].gamemap = data['map_layer'];
  };

  Game.prototype.setAllListCoord = function(list) {
    list.forEach(function(value) {
      var cell, cells, coord, indef, info, _i, _len, _results;
      indef = value[0], cells = value[1];
      _results = [];
      for (_i = 0, _len = cells.length; _i < _len; _i++) {
        cell = cells[_i];
        coord = cell[0];
        info = cell[1] || '';
        _results.push(gamemap_cont.addObject(indef, coord, info));
      }
      return _results;
    }, this);
    return requestAnimationFrame(update, game.canvas);
  };

  Game.prototype.setListCoord = function(list) {
    return list.forEach(function(value) {
      return gamemap_cont.addObject(value[0], value[1], value[2]);
    });
  };

  return Game;

})();

update = function() {
  game.drawAll();
  return requestAnimationFrame(update, game.canvas);
};

Player = (function() {

  function Player() {
    var _this = this;
    document.onkeydown = function(e) {
      e = window.event || e;
      return connect.sendData([_this, 'set_rotate', e.keyCode]);
    };
    document.getElementById('canvas').onmousedown = function(e) {
      var x, y;
      x = parseInt(e.pageX / CELLSIZE);
      y = parseInt(e.pageY / CELLSIZE);
      return connect.sendData([_this, 'set_start_coord', x, y]);
    };
  }

  return Player;

})();

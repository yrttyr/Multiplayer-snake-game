var AbstractGame, Game, Gamemap, GamesList, Layer, MapsList, Player, PlayersList,
  __indexOf = Array.prototype.indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; },
  __hasProp = Object.prototype.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; },
  __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

Gamemap = (function() {

  function Gamemap(SizeX, SizeY, layers_data) {
    var default_tile, name;
    this.SizeX = SizeX;
    this.SizeY = SizeY;
    this.canvas = document.getElementById('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.needDraw = [];
    this.layer = {};
    for (name in layers_data) {
      default_tile = layers_data[name];
      this.layer[name] = new Layer(this, default_tile);
    }
    this.refreshCanvas();
    this.redrawAll();
  }

  Gamemap.prototype.setSizeX = function(x) {
    this.SizeX = x || parseInt(document.getElementById('Size_X').value);
    this.refreshCanvas();
    return this.redrawAll();
  };

  Gamemap.prototype.setSizeY = function(y) {
    this.SizeY = y || parseInt(document.getElementById('Size_Y').value);
    this.refreshCanvas();
    return this.redrawAll();
  };

  Gamemap.prototype.refreshCanvas = function() {
    document.getElementById('Size_X').value = this.SizeX;
    document.getElementById('Size_Y').value = this.SizeY;
    this.canvas.width = this.SizeX * CELLSIZE;
    this.canvas.height = this.SizeY * CELLSIZE;
    return this.canvas.style.display = 'block';
  };

  Gamemap.prototype.addObject = function(indef, coord, info) {
    var layer_name;
    layer_name = game.objects[indef].layer;
    return this.layer[layer_name].set(coord, indef, info);
  };

  Gamemap.prototype.redrawAll = function() {
    var x, y, _ref, _results;
    _results = [];
    for (x = 0, _ref = this.SizeX; 0 <= _ref ? x <= _ref : x >= _ref; 0 <= _ref ? x++ : x--) {
      _results.push((function() {
        var _ref2, _results2;
        _results2 = [];
        for (y = 0, _ref2 = this.SizeY; 0 <= _ref2 ? y <= _ref2 : y >= _ref2; 0 <= _ref2 ? y++ : y--) {
          _results2.push(this.needDraw.push([x, y]));
        }
        return _results2;
      }).call(this));
    }
    return _results;
  };

  Gamemap.prototype.draw = function() {
    var base, base_obj, coord, ground, ground_obj, key, _ref, _results;
    _ref = this.needDraw;
    _results = [];
    for (key in _ref) {
      coord = _ref[key];
      ground = this.layer['ground'].get(coord);
      base = this.layer['base'].get(coord);
      ground_obj = game.objects[ground.indef];
      ground_obj.draw(this.ctx, coord[0], coord[1], ground.type);
      base_obj = game.objects[base.indef];
      base_obj.draw(this.ctx, coord[0], coord[1], base.type);
      _results.push(this.needDraw.splice(key, 1));
    }
    return _results;
  };

  return Gamemap;

})();

Layer = (function() {

  function Layer(container, default_tile_id) {
    this.container = container;
    this.default_tile_id = default_tile_id;
    this.dict = {};
  }

  Layer.prototype.set = function(k, x, type) {
    this.dict[k] = {
      'indef': x,
      'type': type || ''
    };
    return this.container.needDraw.push(k);
  };

  Layer.prototype.setType = function(k, x) {
    if (__indexOf.call(this.dict, k) >= 0) {
      this.dict[k].type = x;
      return this.container.needDraw.push(k);
    } else {
      return console.error('Cell empty', k);
    }
  };

  Layer.prototype.get = function(k) {
    return this.dict[k] || {
      'indef': this.default_tile_id,
      'type': ''
    };
  };

  Layer.prototype.getType = function(k) {
    if (__indexOf.call(this.dict, k) >= 0) return this.dict[k].type;
    return '';
  };

  Layer.prototype.getListIdAndCoord = function() {
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

  return Layer;

})();

GamesList = (function(_super) {

  __extends(GamesList, _super);

  function GamesList() {
    var title,
      _this = this;
    this.div = document.getElementById('games');
    this.maplist = document.getElementById('mapslist');
    this.div.appendChild(this.button('Создать игру', function() {
      if (_this.maplist.value !== '') {
        return connect.sendData([_this, 'create_game', _this.maplist.value]);
      }
    }));
    this.div.appendChild(this.button('Редактор карт', function() {
      if (_this.input.value !== '') {
        connect.sendData([_this, 'create_map', _this.input.value]);
        return _this.input.value = '';
      }
    }));
    title = document.createElement('div');
    title.innerHTML = 'Список игр';
    this.div.appendChild(title);
  }

  GamesList.prototype.createElement = function() {
    return document.createElement('input');
  };

  GamesList.prototype.modifyElement = function(button, indef, data) {
    var _this = this;
    button.type = 'button';
    button.value = indef;
    return button.onclick = function() {
      return connect.sendData([_this, 'subscribe_to', indef]);
    };
  };

  return GamesList;

})(SendList);

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

PlayersList = (function(_super) {

  __extends(PlayersList, _super);

  function PlayersList() {
    this.div = document.getElementById('scoreslist');
  }

  return PlayersList;

})(SendList);

AbstractGame = (function() {

  function AbstractGame() {
    window.game = this;
    this.objects = {};
  }

  AbstractGame.prototype.setMapdata = function(x, y, layer) {
    return this.gamemap = new Gamemap(x, y, layer);
  };

  AbstractGame.prototype.setListDrawdata = function(list) {
    var el, _i, _len, _results;
    _results = [];
    for (_i = 0, _len = list.length; _i < _len; _i++) {
      el = list[_i];
      _results.push(this.setDrawdata(el));
    }
    return _results;
  };

  AbstractGame.prototype.setDrawdata = function(data) {
    return this.objects[data['indef']] = new objectTypes[data['drawtype']](data);
  };

  AbstractGame.prototype.setAllListCoord = function(list) {
    list.forEach(function(value) {
      var cell, cells, coord, indef, info, _i, _len, _results;
      indef = value[0], cells = value[1];
      _results = [];
      for (_i = 0, _len = cells.length; _i < _len; _i++) {
        cell = cells[_i];
        coord = cell[0];
        info = cell[1] || '';
        _results.push(this.gamemap.addObject(indef, coord, info));
      }
      return _results;
    }, this);
    return requestAnimationFrame(this.update, this.canvas);
  };

  AbstractGame.prototype.setListCoord = function(list) {
    return list.forEach(function(value) {
      return this.gamemap.addObject(value[0], value[1], value[2]);
    }, this);
  };

  return AbstractGame;

})();

Game = (function(_super) {

  __extends(Game, _super);

  function Game() {
    this.update = __bind(this.update, this);    Game.__super__.constructor.apply(this, arguments);
    document.getElementById('etitorTools').style.display = 'none';
    document.getElementById('games').style.display = 'block';
  }

  Game.prototype.update = function() {
    this.gamemap.draw();
    return requestAnimationFrame(this.update, this.gamemap.canvas);
  };

  return Game;

})(AbstractGame);

Player = (function() {
  var rotate_keycode;

  rotate_keycode = {
    87: 0,
    68: 1,
    83: 2,
    65: 3
  };

  function Player() {
    var _this = this;
    document.onkeydown = function(e) {
      var rotate;
      e = window.event || e;
      rotate = rotate_keycode[e.keyCode];
      if (typeof rotate !== "undefined") {
        return connect.sendData([_this, 'set_rotate', rotate]);
      }
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

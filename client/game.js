var AbstractGame, Game, Gamemap, GamesList, Layer, MapEditor, MapsList, Player, PlayersList,
  __hasProp = Object.prototype.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; };

Gamemap = (function() {

  function Gamemap(sizeX, sizeY, layers_data) {
    window.gamemap = this;
    this.canvas = document.getElementById('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.needDraw = [];
    this.layer = {};
    this.setSize(sizeX, sizeY);
  }

  Gamemap.prototype.destructor = function() {
    delete window.gamemap;
    return this.canvas.style.display = 'none';
  };

  Gamemap.prototype.setSize = function(SizeX, SizeY) {
    this.SizeX = SizeX;
    this.SizeY = SizeY;
    this.refreshCanvas();
    return this.redrawAll();
  };

  Gamemap.prototype.refreshCanvas = function() {
    document.getElementById('etitorSize_X').value = this.SizeX;
    document.getElementById('etitorSize_Y').value = this.SizeY;
    this.canvas.width = this.SizeX * CELLSIZE;
    this.canvas.height = this.SizeY * CELLSIZE;
    return this.canvas.style.display = 'block';
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

  function Layer(name, default_tile_id) {
    this.name = name;
    this.default_tile_id = default_tile_id;
    this.dict = {};
    gamemap.layer[this.name] = this;
  }

  Layer.prototype.set = function(key, value) {
    var indef, type;
    type = value[0], indef = value[1];
    this.dict[key] = {
      'indef': indef || this.dict[key].indef,
      'type': type || ''
    };
    return gamemap.needDraw.push(key);
  };

  Layer.prototype.removeElement = function(key) {
    delete this.dict[key];
    return gamemap.needDraw.push(key);
  };

  Layer.prototype.get = function(k) {
    return this.dict[k] || {
      'indef': this.default_tile_id,
      'type': ''
    };
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
      if (_this.maplist.value !== '') {
        connect.sendData([_this, 'create_map', _this.maplist.value]);
        return _this.maplist.value = '';
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
    this.scores_tab = document.getElementById('scores_tab');
    this.div = document.createElement('div');
    this.scores_tab.appendChild(this.div);
  }

  PlayersList.prototype.destructor = function() {
    return this.scores_tab.removeChild(this.div);
  };

  return PlayersList;

})(SendList);

AbstractGame = (function() {

  function AbstractGame() {
    window.game = this;
    this.objects = {};
  }

  AbstractGame.prototype.setListDrawdata = function(list) {
    var el, _i, _len;
    for (_i = 0, _len = list.length; _i < _len; _i++) {
      el = list[_i];
      this.setDrawdata(el);
    }
    return this.update();
  };

  AbstractGame.prototype.setDrawdata = function(data) {
    return this.objects[data['indef']] = new objectTypes[data['drawtype']](data);
  };

  AbstractGame.prototype.update = function() {
    gamemap.draw();
    return requestAnimationFrame(game.update, gamemap.canvas);
  };

  return AbstractGame;

})();

Game = (function(_super) {

  __extends(Game, _super);

  function Game() {
    Game.__super__.constructor.apply(this, arguments);
    document.getElementById('scores_tab').style.display = 'block';
  }

  Game.prototype.destructor = function() {
    return document.getElementById('scores_tab').style.display = 'none';
  };

  return Game;

})(AbstractGame);

MapEditor = (function(_super) {

  __extends(MapEditor, _super);

  function MapEditor(name) {
    var _this = this;
    MapEditor.__super__.constructor.apply(this, arguments);
    this.name_div = document.getElementById('etitorMapName');
    this.name_div.value = name;
    this.tiles_div = document.getElementById('etitorTiles');
    document.getElementById('etitorTools').style.display = 'block';
    document.getElementById('games').style.display = 'none';
    document.getElementById('etitorSave').onclick = function(e) {
      return connect.sendData([_this, 'save_map', _this.name_div.value]);
    };
    document.getElementById('etitorExit').onclick = function(e) {
      return connect.sendData([_this, 'exit']);
    };
  }

  MapEditor.prototype.destructor = function() {
    document.getElementById('etitorTools').style.display = 'none';
    return document.getElementById('games').style.display = 'block';
  };

  MapEditor.prototype.setTiles = function(data) {
    var el, indef, key, value, _i, _len, _results;
    this.tiles_div.innerHTML = "";
    _results = [];
    for (key in data) {
      value = data[key];
      for (_i = 0, _len = value.length; _i < _len; _i++) {
        indef = value[_i];
        el = document.createElement('img');
        el.src = this.objects[indef].getSRC();
        el.onclick = (function(indef) {
          return function() {
            return window.player.setParameter('tile', indef);
          };
        })(indef);
        this.tiles_div.appendChild(el);
      }
      _results.push(this.tiles_div.appendChild(document.createElement('br')));
    }
    return _results;
  };

  return MapEditor;

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
    var resize,
      _this = this;
    window.player = this;
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
      return connect.sendData([_this, 'set_coord', x, y]);
    };
    resize = function(e) {
      var x, y;
      x = parseInt(document.getElementById('etitorSize_X').value);
      y = parseInt(document.getElementById('etitorSize_Y').value);
      return connect.sendData([_this, 'set_parameter', 'size', [x, y]]);
    };
    document.getElementById('etitorSize_X').onchange = resize;
    document.getElementById('etitorSize_Y').onchange = resize;
  }

  Player.prototype.setParameter = function(name, value) {
    return connect.sendData([this, 'set_parameter', name, value]);
  };

  return Player;

})();

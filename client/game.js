"use strict";

var needDraw_fill = function(X, Y) {
    for (var x = 0; x <= X - 1; x++) {
        for (var y = 0; y <= Y - 1; y++) {
            game.needDraw.push([x, y]);
        }
    }
};

function Gamemap(default_obj_id) {
    this.dict = {};
    this.default_obj_id = default_obj_id;
    this.set = function(k, x, type) {
        this.dict[k] = {'indef': x, 'type': type || ''};
        game.needDraw.push(k);
    },
    this.setType = function(k, x) {
        if(k in this.dict) {
            this.dict[k].type = x;
            game.needDraw.push(k);
        }
        else {
            console.error('Cell empty', k);
        }
    };
    this.get = function(k) {
        return this.dict[k] || {'indef': this.default_obj_id, 'type': ''};
    };
    this.getType = function(k) {
        if(k in this.dict) {
            return this.dict[k].type
        }
        return ''
    };
    this.getListIdAndCoord = function() {
        var data = [];
        for(var key in this.dict) {
            var indef = this.dict[key].indef;
            if(indef == 0 || indef == 1) {
                continue;
            }
            var coord = key.split(',');
            coord = [parseInt(coord[0]), parseInt(coord[1])];
            if(coord[0] < 0 || coord[0] >= game.SizeX ||
               coord[1] < 0 || coord[1] >= game.SizeY) {
                   console.error(coord);
                    continue;
            }
            data.push([indef, coord]);
        }
        return data
    };
};

function GameList() {
    this.div = document.getElementById('games');
    this.add = function(indef, sizeX, sizeY) {
        var el = document.getElementById(indef);
        if(!el) {
            var el = document.createElement('div');
            el.setAttribute('id', indef);
            this.div.appendChild(el);
        }
        el.innerHTML = '<a href="" onclick="connect.sendData([\'connect_game\',' + indef + ']); return false";>' + indef + '</a>';
    }
};

function Scores() {
    this.div = document.getElementById('scoreslist');
    this.add = function(indef, value) {
        var el = document.getElementById(indef);
        if(!el) {
            //var color = game.objects[indef].color;
            var el = document.createElement('div');
            el.setAttribute('id', indef);
            this.div.appendChild(el);
        }
        el.innerHTML = '' + indef + ' / ' + value;
    };
    this.del = function(indef) {
        var el = document.getElementById(indef);
        if(el) {
            this.div.removeChild(el);
        }
    };
    this.clear = function() {
        if(this.div.hasChildNodes()) {
            while (this.div.childNodes.length >= 1) {
                this.div.removeChild(this.div.firstChild);
            }
        }
    };
};

function createGame() {
    var ml = document.getElementById('mapslist');
    var value = ml.options[ml.selectedIndex].value;
    connect.sendData(['create_game', parseInt(value)]);
}

function Game(layer_info) {
    this.canvas = document.getElementById('canvas');
    this.canvas.onmousedown = canvasKeyDown;
    this.ctx = this.canvas.getContext('2d');

    this.objects = {};
    this.needDraw = [];

    this.gamemap = {};
    for(var name in layer_info) {
        this.gamemap[name] = new Gamemap(layer_info[name]);
    }

    this.setSize = function(x, y) {
        this.SizeX = x;
        this.SizeY = y;
        this.refreshCanvas();
    };

    this.setSizeX = function(x) {
        this.SizeX = x || parseInt(document.getElementById('Size_X').value);
        this.refreshCanvas();
    };

    this.setSizeY = function(y) {
        this.SizeY = y || parseInt(document.getElementById('Size_Y').value);
        this.refreshCanvas();
    };

    this.refreshCanvas = function(x, y) {
        document.getElementById('Size_X').value = this.SizeX;
        document.getElementById('Size_Y').value = this.SizeY;
        this.canvas.width = this.SizeX * CELLSIZE;
        this.canvas.height = this.SizeY * CELLSIZE;
        this.canvas.style.display = 'block';
        needDraw_fill(this.SizeX, this.SizeY);
    };
///////////Game Editor
    this.disableMapEditor = function() {
        this.mapEdit = false;
        document.getElementById('etitorTools').style.display = 'none';
        document.getElementById('games').style.display = 'block';
    };
    this.initMapEditor = function() {
        this.mapEdit = true;
        document.getElementById('etitorTools').style.display = 'block';
        document.getElementById('games').style.display = 'none';
        this.base_div = document.getElementById('base_layer');
        this.ground_div = document.getElementById('ground_layer');
    };
    this.mapEditorAddButton = function(obj, indef) {
        var src = obj.getSRC();
        var el = document.createElement('div');
        if(obj.gamemap == 'base') {
            this.base_div.appendChild(el);
        }
        else {
            this.ground_div.appendChild(el);
        }
        el.innerHTML = '<img src="'+src+'" border=1 align="left" onclick="game.setSelectElement('+indef+'); return false";/>';
    };
    this.setSelectElement = function(num) {
        this.selectElement = num;
    };
    this.saveMap = function() {
        var base = game.gamemap['base'].getListIdAndCoord();
        var ground = game.gamemap['ground'].getListIdAndCoord();
        var data = {'objects': base.concat(ground)};
        data['SizeX'] = game.SizeX;
        data['SizeY'] = game.SizeY;
        connect.sendData(['save_map', data]);
    };
////////////
    this.addObjectInMap = function(indef, coord, info) {
        var gamemap_name = game.objects[indef].gamemap;
        game.gamemap[gamemap_name].set(coord, indef, info);
    };

    this.drawAll = function() {
        for(var key in game.needDraw) {
            var coord = game.needDraw[key];
            var ground = this.gamemap['ground'].get(coord);
            var base = this.gamemap['base'].get(coord);

            var ground_obj = this.objects[ground.indef];
            // Иногда объекты к новой карте не успевают загрузиться
            // Возможно плохое решение и может приводить к большой нагрузке,
            // если объекты долго не смогут загрузиться
            if(ground_obj) {
                ground_obj.draw(coord[0], coord[1], ground.type);
            }

            var base_obj = this.objects[base.indef];
            // И здесь
            if(base_obj) {
                base_obj.draw(coord[0], coord[1], base.type);
            }

            game.needDraw.splice(key, 1);
        }
    };

    this.updateDrawdata = function(data) {
        this.objects[data['indef']] = new objectTypes[data['drawtype']](data);
        this.objects[data['indef']].gamemap = data['map_layer']

        if(game.mapEdit) {
            game.mapEditorAddButton(this.objects[data['indef']], data['indef']);
        }
    };
}

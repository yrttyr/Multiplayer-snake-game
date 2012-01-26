"use strict";

var needDraw_fill = function(X, Y) {
    for (var x = 0; x <= X - 1; x++) {
        for (var y = 0; y <= Y - 1; y++) {
            gamemap_cont.needDraw.push([x, y]);
        }
    }
};

function GamemapContainer(layers) {
    this.canvas = document.getElementById('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.needDraw = [];

    window.gamemap = {};
    for(var name in layers) {
        gamemap[name] = new Gamemap(layers[name]);
    }

    this.setSize = function(x, y) {
        this.SizeX = x;
        this.SizeY = y;
        this.refreshCanvas();
    };

    this.setSizeX = function(x) {
        this.SizeX = x || parseInt(document.getElementById('Size_X').value);
        this.refreshCanvas();
        needDraw_fill(gamemap_cont.SizeX, gamemap_cont.SizeY);
    };

    this.setSizeY = function(y) {
        this.SizeY = y || parseInt(document.getElementById('Size_Y').value);
        this.refreshCanvas();
        needDraw_fill(gamemap_cont.SizeX, gamemap_cont.SizeY);
    };

    this.refreshCanvas = function(x, y) {
        document.getElementById('Size_X').value = this.SizeX;
        document.getElementById('Size_Y').value = this.SizeY;
        this.canvas.width = this.SizeX * CELLSIZE;
        this.canvas.height = this.SizeY * CELLSIZE;
        this.canvas.style.display = 'block';
    };

    this.addObject = function(indef, coord, info) {
        var gamemap_name = game.objects[indef].gamemap;
        gamemap[gamemap_name].set(coord, indef, info);
    };
}

function Gamemap(default_obj_id) {
    this.dict = {};
    this.default_obj_id = default_obj_id;
    this.set = function(k, x, type) {
        this.dict[k] = {'indef': x, 'type': type || ''};
        gamemap_cont.needDraw.push(k);
    },
    this.setType = function(k, x) {
        if(k in this.dict) {
            this.dict[k].type = x;
            gamemap_cont.needDraw.push(k);
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
                    continue;
            }
            data.push([indef, coord]);
        }
        return data
    };
};

function GamesList() {
    this.div = document.getElementById('games');
    this.maplist = document.getElementById('mapslist');

    var button = document.createElement('input');
    button.type = 'button';
    button.value = 'Создать игру';
    button.onclick = function() {
        if(this.maplist.value != '') {
            connect.sendData([this, 'create_game', this.maplist.value]);
        }
    }.bind(this);
    this.div.appendChild(button);

    var button = document.createElement('input');
    button.type = 'button';
    button.value = 'Редактор карт';
    button.onclick = function() {
        if(this.input.value != '') {
            connect.sendData([this, 'create_map', this.input.value]);
            this.input.value = '';
        }
    }.bind(this);
    this.div.appendChild(button);

    var title = document.createElement('div');
    title.innerHTML = 'Список игр';
    this.div.appendChild(title);

    this.set = function(indef, data) {
        var el = document.getElementById(indef);
        if(!el) {
            var el = document.createElement('div');
            el.setAttribute('id', indef);
            this.div.appendChild(el);
        }
        var button = document.createElement('input');
        button.type = 'button';
        button.value = indef;
        button.onclick = function() {
            connect.sendData([this, 'subscribe_to', indef]);
        }.bind(this);
        el.appendChild(button);
    }
};
function MapsList() {
    this.div = document.getElementById('mapslist');
    this.addList = function(list) {
        for(var el in list) {
            this.add(list[el]);
        }
    }
    this.add = function(mapname) {
        var len = this.div.options.length;
        this.div.options[len] = new Option(mapname, mapname);
    }
}

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
        clearDiv(this.div);
    };
};

function Game() {
    window.game = this;
    this.canvas = document.getElementById('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.objects = {};

    document.getElementById('etitorTools').style.display = 'none';
    document.getElementById('games').style.display = 'block';

    this.drawAll = function() {
        for(var key in gamemap_cont.needDraw) {
            var coord = gamemap_cont.needDraw[key];
            var ground = gamemap['ground'].get(coord);
            var base = gamemap['base'].get(coord);

            var ground_obj = this.objects[ground.indef];
            ground_obj.draw(coord[0], coord[1], ground.type);

            var base_obj = this.objects[base.indef];
            base_obj.draw(coord[0], coord[1], base.type);

            gamemap_cont.needDraw.splice(key, 1);
        }
    };
    this.setMapdata = function(x, y, layer) {
        window.gamemap_cont = new GamemapContainer(layer);
        gamemap_cont.setSize(x, y);
        needDraw_fill(x, y);
    };
    this.setListDrawdata = function(list) {
        for(var el in list) {
            this.setDrawdata(list[el]);
        }
    };
    this.setDrawdata = function(data) {
        this.objects[data['indef']] = new objectTypes[data['drawtype']](data);
        this.objects[data['indef']].gamemap = data['map_layer']
    };
    this.setAllListCoord = function(list) {
        list.forEach(function(value) {
            var indef = value[0];
            var cells = value[1];
            for(var key in cells) {
                var coord = cells[key][0];
                var info = cells[key][1] || '';
                gamemap_cont.addObject(indef, coord, info);
            }
        }, this)
        requestAnimationFrame(update, game.canvas);
    };
    this.setListCoord = function(list) {
        list.forEach(function(value) {
            gamemap_cont.addObject(value[0], value[1], value[2]);
        })
    };
}

function update() {
    game.drawAll();
    requestAnimationFrame(update, game.canvas);
}

function clearDiv(div) {
    if(div.hasChildNodes()) {
        while (div.childNodes.length >= 1) {
            div.removeChild(div.firstChild);
        }
    }
}
function Player() {
    // ToDo: Удалять события вместе с объектом
    document.onkeydown = function(e) {
        var e = window.event || e;
        connect.sendData([this, 'set_rotate', e.keyCode]);
    }.bind(this);
    document.getElementById('canvas').onmousedown = function(e) {
        var x = parseInt(e.pageX / CELLSIZE);
        var y = parseInt(e.pageY / CELLSIZE);
        connect.sendData([this, 'set_start_coord', x, y]);
    }.bind(this);
}

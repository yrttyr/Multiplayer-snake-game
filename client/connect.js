"use strict";

if(window.MozWebSocket) {
    window.WebSocket = MozWebSocket;
}

function create_connect() {
    window.connect = new WebSocket("ws://localhost:8080/chat");

    connect.onmessage = function(e) {
        var data = connect.parse(e.data);
        console.log(data);

        switch_parse(data);
    };

    connect.parse = function(data) {
        return JSON.parse(data);
    };

    connect.sendData = function(data) {
        data = JSON.stringify(data);
        console.error('data', data);
        connect.send(data);
    };
}

function switch_parse(data) {
    switch(data[0]) {
        case 'allcoord':
            data[1].forEach(function(value) {
                var indef = value[0];
                var cells = value[1];
                for(var key in cells) {
                    var coord = cells[key][0];
                    var info = cells[key][1] || '';
                    gamemap_cont.addObject(indef, coord, info);
                }
            })
            break

        case 'coord':
            data[1].forEach(function(value) {
                var indef = value[0];
                var coord = value[1];
                var info = value[2] || '';
                gamemap_cont.addObject(indef, coord, info);
            })
            break

        case 'drawdata':
            data[1].forEach(function(value) {
                game.updateDrawdata(value);
            })
            break

        case 'gamelist':
            data[1].forEach(function(value) {
                var indef = value[0];
                var sizeX = value[1];
                var sizeY = value[2];
                gamelist.add(indef, sizeX, sizeY);
            })
            break

        case 'scores':
            var n = data[1];
            var indef = n[0];
            var value = n[1];
            if(value !== '') {
                scores.add(indef, value);
            }
            else {
                scores.del(indef);
            }
            break

        case 'game_status':
            switch(data[1]) {
                case 'play':
                    game.initGame();
                    needDraw_fill(gamemap_cont.SizeX, gamemap_cont.SizeY);
                    break

                case 'map_editor':
                    game.initMapEditor();
                    needDraw_fill(gamemap_cont.SizeX, gamemap_cont.SizeY);
                    break

                default:
                    console.error('неизвестный статус');
            }
            break

        case 'mapdata':
            window.game = new Game();
            scores.clear();

            window.gamemap_cont = new GamemapContainer(data[1][2]);
            gamemap_cont.setSize(data[1][0], data[1][1]);
            break

        case 'mapslist':
            var el = document.getElementById('mapslist');
            for(var key in data[1]) {
                var opt = document.createElement('option');
                opt.innerHTML = data[1][key];
                opt.value = key;
                el.appendChild(opt);
            }
            break

        default:
            console.error('неизвестная команда');
    }
}

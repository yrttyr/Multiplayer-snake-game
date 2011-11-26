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
                    game.addObjectInMap(indef, coord, info);
                }
            })
            break

        case 'drawdata':
            data[1].forEach(function(value) {
                game.updateDrawdata(value);
            })
            break

        case 'coord':
            data[1].forEach(function(value) {
                var indef = value[0];
                var coord = value[1];
                var info = value[2] || '';
                game.addObjectInMap(indef, coord, info);
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
            var color = game.objects[indef].color;
            var value = n[1];
            scores.add(color, value);
            break

        case 'gameinfo':
            window.game = new Game(data[1][2]);
            game.setSize(data[1][0], data[1][1]);
            if(data[1][3]) {
                game.initMapEditor();
            }
            else {
                game.disableMapEditor();
            }
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

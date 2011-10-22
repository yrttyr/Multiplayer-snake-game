"use strict";

if(window.MozWebSocket) {
    window.WebSocket = MozWebSocket;
}

function create_connect() {
    window.connect = new WebSocket("ws://localhost:8080/chat");

    connect.onopen = function(e) {
    };

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

    //connect.onerror = function(e) {alert("error")};
    //connect.onclose = function(e) {alert("closed")};
}

function switch_parse(data) {
    if(data[0] == 'allcoord') {
        data[1].forEach(function(value) {
            var indef = value[0];
            var cells = value[1];
            for(var key in cells) {
                var coord = cells[key][0];
                var info = cells[key][1] || '';
                game.addObjectInMap(indef, coord, info);
            }
        })
    }
    else if(data[0] == 'drawdata') {
        data[1].forEach(function(value) {
            game.updateDrawdata(value);
        })
    }
    else if(data[0] == 'coord') {
        data[1].forEach(function(value) {
            var indef = value[0];
            var coord = value[1];
            var info = value[2] || '';
            game.addObjectInMap(indef, coord, info);
        })
    }
    else if(data[0] == 'gamelist') {
        data[1].forEach(function(value) {
            var indef = value[0];
            var sizeX = value[1];
            var sizeY = value[2];
            gamelist.add(indef, sizeX, sizeY);
        })
    }
    else if(data[0] == 'gameinfo') {
        window.game = new Game();
        game.setSize(data[1][0], data[1][1]);
        if(data[1][2]) {
            game.initMapEditor();
        }
        else {
            game.disableMapEditor();
        }
    }
    else if(data[0] == 'mapslist') {
        var el = document.getElementById('mapslist');
        for(var key in data[1]) {
            var opt = document.createElement('option');
            opt.innerHTML = data[1][key];
            opt.value = key;
            el.appendChild(opt);
        }
    }
}

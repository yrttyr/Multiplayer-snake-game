"use strict";

var objects = {};

if(window.MozWebSocket) {
    window.WebSocket = MozWebSocket;
}

function create_connect() {
    window.connect = new WebSocket("ws://localhost:8080/chat");

    connect.onmessage = function(e) {
        console.log(e.data);
        var data = parseReceive(e.data);
        console.log(data);
        var obj = data[0];
        var fn = data[1];
        var params = data[2];

        fn.apply(obj, params);
    };

    connect.sendData = function(data) {
        data = JSON.stringify(data, function(key, value) {
            if(typeof value == 'object') {
                if(value.indef) {
                    return {'^obj': value.indef}
                }
            }
            return value
        });
        console.error('data', data);
        connect.send(data);
    };
}

function parseReceive(data) {
    var meths = {};
    data = JSON.parse(data, function(key, value) {
        if(value['^class']) {
            return window[value['^class']]
        }
        else if(value['^obj']) {
            var objid = value['^obj'];
            if(! objects[objid]) {
                objects[objid] = {'indef': objid};
            }
            return objects[objid]
        }
        else if(value['^meth']) {
            meths[key] = value['^meth'];
            return value['^meth']
        }
        return value
    });
    for(var key in meths) {
        data[key] = data[key - 1][meths[key]];
    }
    return data
}

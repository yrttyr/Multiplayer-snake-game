"use strict";
function setEvent() {
    document.onkeydown=function(e) {
        var e = window.event || e;
        connect.sendData(['set_rotate', e.keyCode]);
    }
}

//document.onmousedown = canvasKeyDown;
function canvasKeyDown(e) {
    var x = parseInt(e.pageX / CELLSIZE);
    var y = parseInt(e.pageY / CELLSIZE);

    if(game.mapEdit == true) {
        game.addObjectInMap(game.selectElement, [x, y], '');
    }
    else {
        connect.sendData(['set_start_coord', x, y]);
    }
}

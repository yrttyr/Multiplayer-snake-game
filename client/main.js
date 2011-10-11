"use strict";

window.requestAnimationFrame =
    window.requestAnimationFrame        ||
    window.webkitRequestAnimationFrame  ||
    window.mozRequestAnimationFrame     ||
    window.oRequestAnimationFrame       ||
    window.msRequestAnimationFrame      ||
    function(callback, element) {
        window.setTimeout(callback, 1000/60);
    };

window.onload = function() {
    preload.start(imageList, init);
};

function init(images) {
    window.gamelist = GameList();
    window.gamelistdiv = document.getElementById("games");

    window.images = images;
    //images.wall['0'].getImageData(0, 0, 10, 10);
    window.game = new Game();

    window.CELLSIZE = 20;

    create_connect();
    setEvent();
    requestAnimationFrame(update, game.canvas);
}

function update() {
    //game.addObjectInMap();
    game.drawAll();
    requestAnimationFrame(update, game.canvas);
}

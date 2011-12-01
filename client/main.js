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
    window.gamelist = new GameList();
    window.scores = new Scores();

    window.images = images;
    window.game = new Game();
    window.gamemap_cont = new GamemapContainer();

    window.CELLSIZE = 20;

    create_connect();
    setEvents();

    requestAnimationFrame(update, game.canvas);
}

function update() {
    game.drawAll();
    requestAnimationFrame(update, game.canvas);
}

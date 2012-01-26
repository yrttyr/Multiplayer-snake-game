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
    window.images = images;
    window.CELLSIZE = 20;

    create_connect();
    setEvents();
}

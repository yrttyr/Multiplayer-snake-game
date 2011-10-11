"use strict";

var objectTypes = {
    'empty': function(data) {
        return {
            'getSRC': function() {return 'images/other/empty.png';},
            'draw': function(x, y) {}
        }
    },
    'image': function(data) {
        return {
            'getSRC': function() {return images.other[this.image].src;},
            'image': data['image'],
            'draw': function(x, y) {
                game.ctx.drawImage(images.other[this.image], x * CELLSIZE, y * CELLSIZE);
            }
        }
    },
    'wall': function() {
        return {
            'getSRC': function() {return 'images/wall/0.png';},
            'draw': function(x, y) {
                game.ctx.drawImage(images.wall['0'], x * CELLSIZE, y * CELLSIZE);
            }
        }
    },
    'snake': function(par) {
        this.color = par.color;
        this.images = {};
        for(var name in images.snake) {
            var img = images.snake[name];
            var imgdata = getImagedata(img);

            for (var x = 0; x < imgdata.width; x++) {
                for (var y = 0; y < imgdata.height; y++) {
                    var offset = (y * imgdata.width + x) * 4;
                    var r = imgdata.data[offset];
                    var g = imgdata.data[offset + 1];
                    var b = imgdata.data[offset + 2];
                    imgdata.data[offset] = this.color[0] * r / 255;
                    imgdata.data[offset + 1] = this.color[1] * r / 255;
                    imgdata.data[offset + 2] = this.color[2] * r / 255;
                }
            }
            this.images[name] = getConvas(imgdata);
        }
        this.draw = function(x, y, type) {
            if(type in images.snake) {
                game.ctx.drawImage(this.images[type], x * CELLSIZE, y * CELLSIZE);
            }
            else if(type[1] + type[0] in this.images) {
                game.ctx.drawImage(this.images[type[1] + type[0]], x * CELLSIZE, y * CELLSIZE);
            }
        }
    }
};

function getImagedata(img) {
    var canvas = document.createElement("canvas");
    canvas.width = img.width;
    canvas.height = img.height;

    var ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0);

    var myImageData = ctx.getImageData(0, 0, img.width, img.height);
    return myImageData
}

function getConvas(imgdata) {
    var canvas = document.createElement("canvas");
    canvas.width = imgdata.width;
    canvas.height = imgdata.height;

    var ctx = canvas.getContext("2d");
    ctx.putImageData(imgdata, 0, 0);

    return canvas
}

class Gamemap
    constructor: (@SizeX, @SizeY, layers_data) ->
        window.gamemap = @
        @canvas = document.getElementById('canvas')
        @ctx = @canvas.getContext('2d')
        @needDraw = []
        @layer = {}

        @refreshCanvas()
        @redrawAll()

    destructor: ->
        delete window.gamemap

    setSizeX: (x) ->
        @SizeX = x || parseInt(document.getElementById('Size_X').value)
        @refreshCanvas()
        @redrawAll()

    setSizeY: (y) ->
        @SizeY = y || parseInt(document.getElementById('Size_Y').value)
        @refreshCanvas()
        @redrawAll()

    refreshCanvas: ->
        document.getElementById('Size_X').value = @SizeX
        document.getElementById('Size_Y').value = @SizeY
        @canvas.width = @SizeX * CELLSIZE
        @canvas.height = @SizeY * CELLSIZE
        @canvas.style.display = 'block'

    set_mapobject: (indef, coord, info) ->
        layer_name = game.objects[indef].layer
        @layer[layer_name].set(coord, indef, info)

    redrawAll: ->
        for x in [0..@SizeX]
            for y in [0..@SizeY]
                @needDraw.push([x, y])

    draw: ->
        for key, coord of @needDraw
            ground = @layer['ground'].get(coord)
            base = @layer['base'].get(coord)

            ground_obj = game.objects[ground.indef]
            ground_obj.draw(@ctx, coord[0], coord[1], ground.type)

            base_obj = game.objects[base.indef]
            base_obj.draw(@ctx, coord[0], coord[1], base.type)

            @needDraw.splice(key, 1)

class Layer
    constructor: (@name, @default_tile_id) ->
        @dict = {}
        gamemap.layer[@name] = @

    set: (k, x, type) ->
        @dict[k] = {'indef': x, 'type': type || ''}
        gamemap.needDraw.push(k)

    removeElement: (key) ->
        delete @dict[key]
        gamemap.needDraw.push(key)

    setType: (k, x) ->
        if k in @dict
            @dict[k].type = x
            gamemap.needDraw.push(k)
        else
            console.error('Cell empty', k)

    get: (k) ->
        return @dict[k] || {'indef': @default_tile_id, 'type': ''}

    getType: (k) ->
        if k in @dict
            return @dict[k].type
        return ''

    getListIdAndCoord: ->
        data = []
        for key, value of @dict
            indef = value.indef
            if indef == 0 or indef == 1
                continue
            coord = key.split(',')
            coord = [parseInt(coord[0]), parseInt(coord[1])];
            if(coord[0] < 0 or coord[0] >= game.SizeX or
               coord[1] < 0 or coord[1] >= game.SizeY)
                    continue
            data.push([indef, coord])
        return data

class GamesList extends SendList
    constructor: ->
        @div = document.getElementById('games')
        @maplist = document.getElementById('mapslist')

        @div.appendChild(@button('Создать игру', =>
            if @maplist.value != ''
                connect.sendData([@, 'create_game', @maplist.value])))

        @div.appendChild(@button('Редактор карт', =>
            if @input.value != ''
                connect.sendData([@, 'create_map', @input.value])
                @input.value = ''))

        title = document.createElement('div')
        title.innerHTML = 'Список игр'
        @div.appendChild(title)

    createElement: ->
        document.createElement('input')

    modifyElement: (button, indef, data) ->
        button.type = 'button'
        button.value = indef
        button.onclick = =>
            connect.sendData([@, 'subscribe_to', indef])

class MapsList
    constructor: ->
        @div = document.getElementById('mapslist');

    addList: (list) ->
        for el in list
            this.add el

    add: (mapname) ->
        len = @div.options.length
        @div.options[len] = new Option(mapname, mapname)

class PlayersList extends SendList
    constructor: ->
        @div = document.getElementById('scoreslist')

class AbstractGame
    constructor: ->
        window.game = @
        @objects = {}

    destructor: ->
        delete window.game

    setListDrawdata: (list) ->
        for el in list
            @setDrawdata(el)

    setDrawdata: (data) ->
        @objects[data['indef']] = new objectTypes[data['drawtype']](data)

    setAllListCoord: (list) ->
        list.forEach((value) ->
            [indef, cells] = value
            for cell in cells
                coord = cell[0]
                info = cell[1] || ''
                gamemap.set_mapobject(indef, coord, info)
        )
        requestAnimationFrame(@update, @canvas);

class Game extends AbstractGame
    constructor: ->
        super
        document.getElementById('etitorTools').style.display = 'none'
        document.getElementById('games').style.display = 'block'

    update: =>
        gamemap.draw()
        requestAnimationFrame(@update, gamemap.canvas)

class Player
    rotate_keycode = {87: 0, 68: 1, 83: 2, 65: 3}
    constructor: ->
        document.onkeydown = (e) =>
            e = window.event || e
            rotate = rotate_keycode[e.keyCode]
            if typeof rotate != "undefined"
                connect.sendData([@, 'set_rotate', rotate])

        document.getElementById('canvas').onmousedown = (e) =>
            x = parseInt(e.pageX / CELLSIZE)
            y = parseInt(e.pageY / CELLSIZE)
            connect.sendData([@, 'set_start_coord', x, y])

needDraw_fill = (X, Y) ->
    for x in [0..X]
        for y in [0..Y]
            gamemap_cont.needDraw.push([x, y])

class GamemapContainer
    constructor: (layers) ->
        @canvas = document.getElementById('canvas')
        @ctx = @canvas.getContext('2d')
        @needDraw = []

        window.gamemap = {}
        for name, layer of layers
            gamemap[name] = new Gamemap(layer)

    setSize: (@SizeX, @SizeY) ->
        @refreshCanvas()

    setSizeX: (x) ->
        @SizeX = x || parseInt(document.getElementById('Size_X').value)
        @refreshCanvas()
        needDraw_fill(gamemap_cont.SizeX, gamemap_cont.SizeY)

    setSizeY: (y) ->
        @SizeY = y || parseInt(document.getElementById('Size_Y').value)
        @refreshCanvas()
        needDraw_fill(gamemap_cont.SizeX, gamemap_cont.SizeY)

    refreshCanvas: ->
        document.getElementById('Size_X').value = @SizeX
        document.getElementById('Size_Y').value = @SizeY
        @canvas.width = @SizeX * CELLSIZE
        @canvas.height = @SizeY * CELLSIZE
        @canvas.style.display = 'block'

    addObject: (indef, coord, info) ->
        gamemap_name = game.objects[indef].gamemap
        gamemap[gamemap_name].set(coord, indef, info)


class Gamemap
    constructor: (@default_obj_id) ->
        @dict = {}
    set: (k, x, type) ->
        @dict[k] = {'indef': x, 'type': type || ''}
        gamemap_cont.needDraw.push(k)

    setType: (k, x) ->
        if k in @dict
            @dict[k].type = x
            gamemap_cont.needDraw.push(k)
        else
            console.error('Cell empty', k)

    get: (k) ->
        return @dict[k] || {'indef': @default_obj_id, 'type': ''}

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

        button = document.createElement('input')
        button.type = 'button'
        button.value = 'Создать игру'
        button.onclick = =>
            if @maplist.value != ''
                connect.sendData([@, 'create_game', @maplist.value])
        @div.appendChild(button)

        button = document.createElement('input')
        button.type = 'button'
        button.value = 'Редактор карт'
        button.onclick = =>
            if @input.value != ''
                connect.sendData([@, 'create_map', @input.value])
                @input.value = ''
        @div.appendChild(button);

        title = document.createElement('div')
        title.innerHTML = 'Список игр'
        @div.appendChild(title)

    createElement: () ->
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

class Game
    constructor: ->
        window.game = @
        @canvas = document.getElementById('canvas')
        @ctx = @canvas.getContext('2d')
        @objects = {}

        document.getElementById('etitorTools').style.display = 'none'
        document.getElementById('games').style.display = 'block'

    drawAll: ->
        for key, coord of gamemap_cont.needDraw
            ground = gamemap['ground'].get(coord)
            base = gamemap['base'].get(coord)

            ground_obj = @objects[ground.indef]
            ground_obj.draw(coord[0], coord[1], ground.type)

            base_obj = @objects[base.indef]
            base_obj.draw(coord[0], coord[1], base.type)

            gamemap_cont.needDraw.splice(key, 1)

    setMapdata: (x, y, layer) ->
        window.gamemap_cont = new GamemapContainer(layer)
        gamemap_cont.setSize(x, y)
        needDraw_fill(x, y)

    setListDrawdata: (list) ->
        for el in list
            @setDrawdata(el)

    setDrawdata: (data) ->
        @objects[data['indef']] = new objectTypes[data['drawtype']](data)
        @objects[data['indef']].gamemap = data['map_layer']

    setAllListCoord: (list) ->
        list.forEach((value) ->
            [indef, cells] = value
            for cell in cells
                coord = cell[0]
                info = cell[1] || ''
                gamemap_cont.addObject(indef, coord, info)
        , @)
        requestAnimationFrame(update, game.canvas);

    setListCoord: (list) ->
        list.forEach((value) ->
            gamemap_cont.addObject(value[0], value[1], value[2])
        )

update = ->
    game.drawAll()
    requestAnimationFrame(update, game.canvas)

class Player
    # ToDo: Удалять события вместе с объектом
    constructor: ->
        document.onkeydown = (e) =>
            e = window.event || e
            connect.sendData([@, 'set_rotate', e.keyCode])

        document.getElementById('canvas').onmousedown = (e) =>
            x = parseInt(e.pageX / CELLSIZE)
            y = parseInt(e.pageY / CELLSIZE)
            connect.sendData([@, 'set_start_coord', x, y])

class Gamemap
    constructor: (sizeX, sizeY, layers_data) ->
        window.gamemap = @
        @canvas = document.getElementById('canvas')
        @ctx = @canvas.getContext('2d')
        @needDraw = []
        @layer = {}
        @setSize(sizeX, sizeY)

    destructor: ->
        delete window.gamemap

    setSize: (@SizeX, @SizeY) ->
        @refreshCanvas()
        @redrawAll()

    refreshCanvas: ->
        document.getElementById('etitorSize_X').value = @SizeX
        document.getElementById('etitorSize_Y').value = @SizeY
        @canvas.width = @SizeX * CELLSIZE
        @canvas.height = @SizeY * CELLSIZE
        @canvas.style.display = 'block'

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

    get: (k) ->
        return @dict[k] || {'indef': @default_tile_id, 'type': ''}

class GamesList extends SendList
    constructor: ->
        @div = document.getElementById('games')
        @maplist = document.getElementById('mapslist')

        @div.appendChild(@button('Создать игру', =>
            if @maplist.value != ''
                connect.sendData([@, 'create_game', @maplist.value])))

        @div.appendChild(@button('Редактор карт', =>
            if @maplist.value != ''
                connect.sendData([@, 'create_map', @maplist.value])
                @maplist.value = ''))

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
        @scores_tab = document.getElementById('scores_tab')
        @div = document.createElement('div')
        @scores_tab.appendChild(@div)

    destructor: ->
        @scores_tab.removeChild(@div)

class AbstractGame
    constructor: ->
        window.game = @
        @objects = {}

    destructor: ->
        delete window.game

    setListDrawdata: (list) ->
        for el in list
            @setDrawdata(el)
        requestAnimationFrame(@update, @canvas);

    setDrawdata: (data) ->
        @objects[data['indef']] = new objectTypes[data['drawtype']](data)

    update: =>
        gamemap.draw()
        requestAnimationFrame(@update, gamemap.canvas)

class Game extends AbstractGame
    constructor: ->
        super
        document.getElementById('etitorTools').style.display = 'none'
        document.getElementById('games').style.display = 'block'

class MapEditor extends AbstractGame
    constructor: (name) ->
        super
        @name_div = document.getElementById('etitorMapName')
        @name_div.value = name
        @tiles_div = document.getElementById('etitorTiles')
        document.getElementById('etitorTools').style.display = 'block'
        document.getElementById('games').style.display = 'none'

        document.getElementById('etitorSave').onclick = (e) =>
            connect.sendData([@, 'save_map', @name_div.value])

    setTiles: (data)->
        @tiles_div.innerHTML = ""
        for key, value of data
            for indef in value
                el = document.createElement('img')
                el.src = @objects[indef].getSRC()
                el.onclick = (
                    (indef) ->
                        -> window.player.setParameter('tile', indef)
                    )(indef)

                @tiles_div.appendChild(el)
            @tiles_div.appendChild(document.createElement('br'))

class Player
    rotate_keycode = {87: 0, 68: 1, 83: 2, 65: 3}
    constructor: ->
        window.player = @
        document.onkeydown = (e) =>
            e = window.event || e
            rotate = rotate_keycode[e.keyCode]
            if typeof rotate != "undefined"
                connect.sendData([@, 'set_rotate', rotate])

        document.getElementById('canvas').onmousedown = (e) =>
            x = parseInt(e.pageX / CELLSIZE)
            y = parseInt(e.pageY / CELLSIZE)
            connect.sendData([@, 'set_coord', x, y])

        resize = (e) =>
            x = parseInt(document.getElementById('etitorSize_X').value)
            y = parseInt(document.getElementById('etitorSize_Y').value)
            connect.sendData([@, 'set_parameter', 'size', [x, y]])

        document.getElementById('etitorSize_X').onchange = resize
        document.getElementById('etitorSize_Y').onchange = resize

    setParameter: (name, value) ->
        connect.sendData([@, 'set_parameter', name, value])

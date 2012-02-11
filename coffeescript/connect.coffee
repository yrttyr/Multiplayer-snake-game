if window.MozWebSocket
    window.WebSocket = MozWebSocket

objects = {}

create_connect = ->
    window.connect = new WebSocket("ws://localhost:8080/chat")

    connect.onmessage = (e) ->
        console.log e.data
        data = parseReceive e.data
        console.log data

        [fn, params] = data
        fn(params...)

    connect.sendData = (data) ->
        data = JSON.stringify(data, encode)
        console.error('data', data)
        connect.send data

encode = (key, value) ->
    if typeof value == 'object'
        if value.indef
            return {'^obj': value.indef}
    return value

parseReceive = (data) ->
    data = JSON.parse(data, decode)
    return data

decode = (key, value) ->
    if value['^class']
        return createObject(window[value['^class']])
    else if value['^obj']
        return objects[value['^obj']]
    else if value['^meth']
        return callMeth(value['^meth']...)
    return value

createObject = (constr) ->
    (indef) ->
        objects[indef] = (args...) ->
            objects[indef] = new constr(args...)
            objects[indef].indef = indef
            console.log('objects now', indef)

callMeth = (indef, fn_name) ->
    (args...) ->
        obj = objects[indef]
        obj[fn_name](args...)

class SendList
    set: (indef, data) ->
        el = @getElement(indef)
        if not el
            el = @createElement()
            el.setAttribute('id', indef)
            @saveElement(el)
        @modifyElement(el, indef, data...)

    getElement: (indef) ->
        document.getElementById(indef)

    createElement: ->
        document.createElement('div')

    saveElement: (el) ->
        @div.appendChild(el)

    modifyElement: (el, indef, data) ->
        el.innerHTML = data

    removeElement: (indef) ->
        @div.removeChild(@getElement(indef))

    button: (value, onclick) ->
        button = document.createElement('input')
        button.type = 'button'
        button.value = value
        button.onclick = onclick
        return button

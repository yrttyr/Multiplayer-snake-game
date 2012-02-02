if window.MozWebSocket
    window.WebSocket = MozWebSocket

objects = {}

create_connect = ->
    window.connect = new WebSocket("ws://localhost:8080/chat")

    connect.onmessage = (e) ->
        console.log e.data
        data = parseReceive e.data
        console.log data
        [obj, fn, params] = data

        fn.apply(obj, params)

    connect.sendData = (data) ->
        data = JSON.stringify(data, encode)
        console.error('data', data)
        connect.send data

encode = (key, value) ->
    if typeof value == 'object'
        if value.indef
            return {'^obj': value.indef}
    return value

meths = {}
parseReceive = (data) ->
    data = JSON.parse(data, decode)
    for key, value of meths
        data[key] = data[key - 1][value]
    window.meths = {}
    data

decode = (key, value) ->
    if value['^class']
        return window[value['^class']]
    else if value['^obj']
        objid = value['^obj']
        if not objects[objid]
            objects[objid] = {'indef': objid}
        return objects[objid]
    else if value['^meth']
        meths[key] = value['^meth'];
        return value['^meth']
    return value

class SendList
    set: (indef, data) ->
        el = @getElement(indef)
        if not el
            el = @createElement()
            el.setAttribute('id', indef)
            @saveElement(el)
        @modifyElementdata.apply([el, indef].concat(data))

    getElement: (indef) ->
        document.getElementById(indef)

    createElement: (indef) ->
        document.createElement('div')

    saveElement: (el) ->
        @div.appendChild(el)

    modifyElement: (el, indef, data) ->
        el.innerHTML = data

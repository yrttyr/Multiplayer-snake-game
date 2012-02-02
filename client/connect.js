var SendList, create_connect, decode, encode, meths, objects, parseReceive;

if (window.MozWebSocket) window.WebSocket = MozWebSocket;

objects = {};

create_connect = function() {
  window.connect = new WebSocket("ws://localhost:8080/chat");
  connect.onmessage = function(e) {
    var data, fn, obj, params;
    console.log(e.data);
    data = parseReceive(e.data);
    console.log(data);
    obj = data[0], fn = data[1], params = data[2];
    return fn.apply(obj, params);
  };
  return connect.sendData = function(data) {
    data = JSON.stringify(data, encode);
    console.error('data', data);
    return connect.send(data);
  };
};

encode = function(key, value) {
  if (typeof value === 'object') {
    if (value.indef) {
      return {
        '^obj': value.indef
      };
    }
  }
  return value;
};

meths = {};

parseReceive = function(data) {
  var key, value;
  data = JSON.parse(data, decode);
  for (key in meths) {
    value = meths[key];
    data[key] = data[key - 1][value];
  }
  window.meths = {};
  return data;
};

decode = function(key, value) {
  var objid;
  if (value['^class']) {
    return window[value['^class']];
  } else if (value['^obj']) {
    objid = value['^obj'];
    if (!objects[objid]) {
      objects[objid] = {
        'indef': objid
      };
    }
    return objects[objid];
  } else if (value['^meth']) {
    meths[key] = value['^meth'];
    return value['^meth'];
  }
  return value;
};

SendList = (function() {

  function SendList() {}

  SendList.prototype.set = function(indef, data) {
    var el;
    el = this.getElement(indef);
    if (!el) {
      el = this.createElement();
      el.setAttribute('id', indef);
      this.saveElement(el);
    }
    return this.modifyElementdata.apply([el, indef].concat(data));
  };

  SendList.prototype.getElement = function(indef) {
    return document.getElementById(indef);
  };

  SendList.prototype.createElement = function(indef) {
    return document.createElement('div');
  };

  SendList.prototype.saveElement = function(el) {
    return this.div.appendChild(el);
  };

  SendList.prototype.modifyElement = function(el, indef, data) {
    return el.innerHTML = data;
  };

  return SendList;

})();

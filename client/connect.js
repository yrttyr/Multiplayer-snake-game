var SendList, callMeth, createObject, create_connect, decode, encode, objects, parseReceive,
  __slice = Array.prototype.slice;

if (window.MozWebSocket) window.WebSocket = MozWebSocket;

objects = {};

create_connect = function() {
  window.connect = new WebSocket("ws://localhost:8080/chat");
  connect.onmessage = function(e) {
    var data, fn, params;
    console.log(e.data);
    data = parseReceive(e.data);
    console.log(data);
    fn = data[0], params = data[1];
    return fn.apply(null, params);
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

parseReceive = function(data) {
  data = JSON.parse(data, decode);
  return data;
};

decode = function(key, value) {
  if (value['^class']) {
    return createObject(value['^class']);
  } else if (value['^obj']) {
    return objects[value['^obj']];
  } else if (value['^meth']) {
    return callMeth.apply(null, value['^meth']);
  }
  return value;
};

createObject = function(className) {
  return function(indef, args) {
    var cls, inst;
    cls = window[className];
    inst = (function(func, args, ctor) {
      ctor.prototype = func.prototype;
      var child = new ctor, result = func.apply(child, args);
      return typeof result === "object" ? result : child;
    })(cls, args, function() {});
    inst.indef = indef;
    return objects[indef] = inst;
  };
};

callMeth = function(indef, fn_name) {
  if (fn_name === 'destructor') {
    return function() {
      var args, obj;
      args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
      obj = objects[indef];
      try {
        obj[fn_name].apply(obj, args);
      } catch (error) {

      }
      return delete objects[indef];
    };
  } else {
    return function() {
      var args, obj;
      args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
      obj = objects[indef];
      return obj[fn_name].apply(obj, args);
    };
  }
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
    return this.modifyElement.apply(this, [el, indef].concat(__slice.call(data)));
  };

  SendList.prototype.getElement = function(indef) {
    return document.getElementById(indef);
  };

  SendList.prototype.createElement = function() {
    return document.createElement('div');
  };

  SendList.prototype.saveElement = function(el) {
    return this.div.appendChild(el);
  };

  SendList.prototype.modifyElement = function(el, indef, data) {
    return el.innerHTML = data;
  };

  SendList.prototype.removeElement = function(indef) {
    return this.div.removeChild(this.getElement(indef));
  };

  SendList.prototype.button = function(value, onclick) {
    var button;
    button = document.createElement('input');
    button.type = 'button';
    button.value = value;
    button.onclick = onclick;
    return button;
  };

  return SendList;

})();

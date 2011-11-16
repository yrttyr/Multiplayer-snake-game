#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import WeakValueDictionary, WeakSet, ref
from collections import namedtuple, defaultdict
import json

wrappers = WeakValueDictionary()

def send_cls(group_name=None, singleton=False):
    def inner(_cls):
        if group_name is None:
            group_name_local = _cls.__name__
        else:
            group_name_local = group_name

        send_meth, recv_meth = _get_methods(_cls)
        for meth in send_meth:
            _replace_sendfun(meth)
        for meth in recv_meth:
            _replace_recvfun(meth)

        recvmeth_names = [meth.name for meth in recv_meth]
        call_with_conn = getattr(_cls, 'call_with_conn', ())

        _replace_init(_cls, group_name_local, recvmeth_names,
                     call_with_conn, singleton)
        _replace_del(_cls)
        return _cls
    return inner

def _get_methods(cls):
    send = []
    recv = []
    for atr_name in cls.__dict__.keys():
        atr = getattr(cls, atr_name)
        if hasattr(atr, '_sendmeth') and atr._sendmeth:
            send.append(atr)
        elif hasattr(atr, '_recvmeth') and atr._recvmeth:
            recv.append(atr)
    return send, recv

def _replace_init(_cls, group_name, recvmeth_names,
                 call_with_conn, singleton):
    _old_init = _cls.__init__
    def _initfun(self, *args, **kwargs):
        if id(self) not in wrappers: # Защита при вызове __init__ родителя
            _send_obj = SendObj(self, group_name,
                                recvmeth_names, call_with_conn)
            wrappers[id(self)] = _send_obj
            if singleton:
                wrappers[_cls.__name__] = _send_obj
        _old_init(self, *args, **kwargs)
    _cls.__init__ = _initfun

def _replace_del(_cls):
    _old_del = getattr(_cls, '__del__', None)
    if _old_del:
        def _delfun(self, *args, **kwargs):
            if id(self) in wrappers:
                wrappers[id(self)].kill()
            _old_del(self, *args, **kwargs)
    else:
        def _delfun(self, *args, **kwargs):
            if id(self) in wrappers:
                wrappers[id(self)].kill()
    _cls.__del__ = _delfun

def _replace_sendfun(_fun):
    def _sendfun(self, *args, **kwargs):
        if '_send_to' in kwargs:
            _send_to = kwargs['_send_to']
            del kwargs['_send_to']
        else:
            _send_to = []
        data = _fun(self, *args, **kwargs)
        if not data:
            return
        wrappers[id(self)].send((_fun.name, data), _send_to)
    setattr(_fun.im_class, _fun.__name__, _sendfun)

def _replace_recvfun(_fun):
    def _recvfun(self, *args, **kwargs):
        return _fun(self, *args, **kwargs)  # Нужно ловля экцептов на неправильные аргументы
    setattr(_fun.im_class, _fun.__name__, _recvfun)

def send_meth(name):
    def inner(_meth):
        _meth._sendmeth = True
        _meth.name = name
        return _meth
    return inner

def recv_meth(name=False):
    def inner(_meth):
        _meth._recvmeth = True
        if name:
            _meth.name = name
        else:
            _meth.name = _meth.__name__
        return _meth
    return inner

class SendObj(object):
    _keeper = set()
    def __init__(self, obj, group_name, recvmeth_names, call_with_conn):
        self._obj = ref(obj)
        self.keep_obj = None
        self.group_name = group_name
        self.recvmeth_names = recvmeth_names
        self.call_with_conn = call_with_conn
        self.subscribers = WeakSet()
        self._keeper.add(self)

    @property
    def obj(self):
        return self._obj()

    def kill(self):
        self._keeper.remove(self)

    def subscribe(self, sub):
        self.subscribers.add(sub)
        for meth_name in self.call_with_conn:
            getattr(self.obj, meth_name)(_send_to=[sub])

        if self.subscribers:
            self.keep_obj = self.obj

    def unsubscribe(self, sub=None):
        if sub:
            self.subscribers.discard(sub)

        if not self.subscribers:
            self.keep_obj = None

    def send(self, data, sendto):
        if not sendto:
            sendto = self.subscribers

        data = self.packager(data)
        tup = tuple(sendto)
        for sub in tup:
            sub.send(data)

    def packager(self, data):
        return json.dumps(data, separators=(',', ':'))

class Subscriber(object):
    def __init__(self, connect):
        self.connect = connect
        self.send_obj = dict()
        self.call()

    def get_sendobj(self, name):
        return self.send_obj[name].obj

    def subscribe(self, send_obj):
        send_obj = self._get_send_obj(send_obj)
        group_name = send_obj.group_name
        if group_name in self.send_obj:
            self.unsubscribe(group_name)

        send_obj.subscribe(self)
        self.send_obj[group_name] = send_obj

    def unsubscribe(self, send_obj):
        send_obj = self._get_send_obj(send_obj, True)
        group_name = send_obj.group_name
        self.send_obj[group_name].unsubscribe(self)
        del self.send_obj[group_name]

    def _get_send_obj(self, data, unsub=False):
        if isinstance(data, basestring):
            if unsub:
                return self.send_obj[data]
            return wrappers[data]
        elif isinstance(data, int):
            return wrappers[data]
        elif id(data) in wrappers:
            return wrappers[id(data)]
        return data

    def send(self, data):
        try:
            self.connect.send(data)
        except EnvironmentError as e:
            self.connect.subscriber = None
            print 'end error'

    def __del__(self):
        for obj in self.send_obj.values():
            obj.unsubscribe()

    def call(self):
        pass

    def recv(self, data):
        print 'data', data, type(data)
        data = data.decode("utf-8")
        print 'decode', data, type(data)

        data = json.loads(data)
        fun_name, attr = data[0], data[1:]
        print fun_name, attr
        for send_obj in self.send_obj.values():
            if fun_name in send_obj.recvmeth_names:
                getattr(send_obj.obj, fun_name)(self, *attr)
                break
        else:
            print fun_name, attr
            raise

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from weakref import WeakValueDictionary, WeakSet, ref
from collections import namedtuple
from errno import EBADF
import json

class Sender(WeakValueDictionary):
    def send_cls(self, singleton=False):
        def inner(_cls):
            send_meth, recv_meth = self.get_methods(_cls)
            for meth in send_meth:
                self.replace_sendfun(meth)
            for meth in recv_meth:
                self.replace_recvfun(meth)

            recvmeth_names = [meth.name for meth in recv_meth]
            self.replace_init(_cls, recvmeth_names, singleton)
            self.replace_del(_cls)
            return _cls
        return inner

    def get_methods(self, cls):
        send = []
        recv = []
        for atr_name in cls.__dict__.keys():
            atr = getattr(cls, atr_name)
            if hasattr(atr, '_sendmeth') and atr._sendmeth:
                send.append(atr)
            elif hasattr(atr, '_recvmeth') and atr._recvmeth:
                recv.append(atr)
        return send, recv

    def replace_init(_sender, _cls, recvmeth_names, singleton):
        _old_init = _cls.__init__
        def tmp(self, *args, **kwargs):
            _send_obj = SendObj(self, recvmeth_names)
            _sender[id(self)] = _send_obj
            if singleton:
                _sender[_cls.__name__] = _send_obj
            _old_init(self, *args, **kwargs)
        _cls.__init__ = tmp

    def replace_del(_sender, _cls):
        _old_del = getattr(_cls, '__del__', None)
        if _old_del:
            def tmp(self, *args, **kwargs):
                _sender[id(self)].kill()
                _old_del(self, *args, **kwargs)
        else:
            def tmp(self, *args, **kwargs):
                _sender[id(self)].kill()
        _cls.__del__ = tmp

    def replace_sendfun(_sender, _fun):
        def tmp(self, *args, **kwargs):
            data = _fun(self, *args, **kwargs)
            if not data:
                return
            _sender[id(self)].send((_fun.name, data))
        setattr(_fun.im_class, _fun.__name__, tmp)

    def replace_recvfun(_sender, _fun):
        def tmp(self, *args, **kwargs):
            return _fun(self, *args, **kwargs)  # Нужно ловля экцептов на неправильные аргументы
        setattr(_fun.im_class, _fun.__name__, tmp)

    def send_meth(self, name):
        def inner(_meth):
            _meth._sendmeth = True
            _meth.name = name
            return _meth
        return inner

    def recv_meth(self, name=False):
        def inner(_meth):
            _meth._recvmeth = True
            if name:
                _meth.name = name
            else:
                _meth.name = _meth.__name__
            return _meth
        return inner

sender = Sender()

class SendObj(object):
    list_ = []
    def __init__(self, obj, recvmeth_names):
        self._obj = ref(obj)
        self.keep_obj = None
        self.recvmeth_names = recvmeth_names
        self.subscribers = WeakSet()
        self.list_.append(self)

    @property
    def obj(self):
        return self._obj()

    def kill(self):
        self.list_.remove(self)

    def subscribe(self, sub):
        print 'sub'
        self.subscribers.add(sub)
        self.obj.send_start()   #Отправляеться всем, непорядок

        if self.subscribers:
            #print('player keep')
            self.keep_obj = self.obj

    def unsubscribe(self, sub=None):
        if sub:
            self.subscribers.discard(sub)

        #print type(self.obj).__name__, self.subscribers
        if not self.subscribers:
            #print('player not keep')
            self.keep_obj = None

        #print type(self.obj).__name__
        #if sys.getrefcount(self.obj) == 2:
        #    self.obj = None
        #    self.list_.remove(self)

    def __del__(self):
        print 'del send_obj'

    def send(self, data):
        self._send(data, self.subscribers)

    def _send(self, data, pl_list):
        data = self.packager(data)
        tup = tuple(pl_list)
        for sub in tup:
        #while(pl_list):
            sub.send(data)

    def packager(self, data):
        return json.dumps(data, separators=(',', ':'))

class Subscriber(object):
    def __init__(self, connect):
        self.connect = connect  # сделать weakref
        self.send_obj = WeakValueDictionary()
        self.call()

    def get_sendobj(self, name):
        return self.send_obj[name].obj

    def subscribe(self, send_obj):
        if isinstance(send_obj, basestring):
            send_obj = sender[send_obj]
        elif isinstance(send_obj, int):
            send_obj = sender[send_obj]
        else:
            send_obj = sender[id(send_obj)]
        send_obj.subscribe(self)
        class_name = type(send_obj.obj).__name__
        if class_name in self.send_obj:
            self.send_obj[class_name].unsubscribe(self)
        self.send_obj[class_name] = send_obj #второй словарь с id для не синглтонов

    def send(self, data):
        try:
            self.connect.send(data)
        except EnvironmentError as e:
            print 'EBADF error'
            print e
            self.connect.subscriber = None
            print 'end error'

    def __del__(self):
        print 'sub del'
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

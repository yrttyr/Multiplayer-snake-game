#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import WeakValueDictionary, WeakSet, ref
from collections import namedtuple, defaultdict
import json

class Sender(WeakValueDictionary):
    def send_cls(self, group_name=None, singleton=False):
        def inner(_cls):
            if group_name is None:
                group_name_local = _cls.__name__
            else:
                group_name_local = group_name
            print group_name_local

            send_meth, recv_meth = self.get_methods(_cls)
            for meth in send_meth:
                self.replace_sendfun(meth)
            for meth in recv_meth:
                self.replace_recvfun(meth)

            recvmeth_names = [meth.name for meth in recv_meth]
            call_with_conn = getattr(_cls, 'call_with_conn', ())

            self.replace_init(_cls, group_name_local, recvmeth_names,
                              call_with_conn, singleton)
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

    def replace_init(_sender, _cls, group_name, recvmeth_names,
                     call_with_conn, singleton):
        _old_init = _cls.__init__
        def tmp(self, *args, **kwargs):
            if id(self) not in _sender: # Защита при вызове __init__ родителя
                _send_obj = SendObj(self, group_name, recvmeth_names, call_with_conn)
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
            if '_send_to' in kwargs:
                _send_to = kwargs['_send_to']
                del kwargs['_send_to']
            else:
                _send_to = []
            data = _fun(self, *args, **kwargs)
            if not data:
                return
            _sender[id(self)].send((_fun.name, data), _send_to)
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
    def __init__(self, obj, group_name, recvmeth_names, call_with_conn):
        self._obj = ref(obj)
        self.keep_obj = None
        self.group_name = group_name
        self.recvmeth_names = recvmeth_names
        self.call_with_conn = call_with_conn
        print 'call_with_conn', type(self.obj).__name__, self.call_with_conn
        self.subscribers = WeakSet()
        self.list_.append(self)

    @property
    def obj(self):
        return self._obj()

    def kill(self):
        self.list_.remove(self)

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

    def __del__(self):
        print 'del send_obj'

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
        self.send_obj = WeakValueDictionary()
        self.call()

    def get_sendobj(self, name):
        return self.send_obj[name].obj

    def subscribe(self, send_obj):
        send_obj = self._get_send_obj(send_obj)
        group_name = send_obj.group_name
        if group_name in self.send_obj:
            self.send_obj[group_name].unsubscribe(self)
            print 'call unsub'
        send_obj.subscribe(self)
        self.send_obj[group_name] = send_obj
        print 'sub', group_name

    def _get_send_obj(self, data):
        if isinstance(data, basestring):
            return sender[data]
        elif isinstance(data, int):
            return sender[data]
        elif id(data) in sender:
            return sender[id(data)]
        return data

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

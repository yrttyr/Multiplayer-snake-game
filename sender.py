#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import WeakValueDictionary, WeakSet, ref
from collections import namedtuple, defaultdict
import json

wrappers = WeakValueDictionary()

def sendto(to, senders, class_name, func_name):
    for sender in senders:
        getattr(sender.get_obj(class_name), func_name)(_send_to=to)

def send_cls(name=None, singleton=False):
    def inner(_cls):
        if name is None:
            name_local = _cls.__name__
        else:
            name_local = name

        send_meth, recv_meth = _get_methods(_cls)
        for meth in send_meth:
            _replace_sendfun(meth)
        for meth in recv_meth:
            _replace_recvfun(meth)

        recvmeth_names = [meth.name for meth in recv_meth]
        call_with_conn = getattr(_cls, 'call_with_conn', ())

        _replace_init(_cls, name_local, recvmeth_names,
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

def _replace_init(_cls, name, recvmeth_names,
                 call_with_conn, singleton):
    _old_init = _cls.__init__
    def _initfun(self, *args, **kwargs):
        if id(self) not in wrappers: # Защита при вызове __init__ родителя
            _wrapper = Wrapper(self, name, recvmeth_names,
                               call_with_conn)
            wrappers[id(self)] = _wrapper
            if singleton:
                wrappers[name] = _wrapper
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
            _send_to = None
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

class Wrapper(object):
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

    def __len__(self):
        return len(self.subscribers)

    def __iter__(self):
        for i in self.subscribers:
            yield i

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
        data = self.packager(data)

        if sendto is None:
            sendto = self.subscribers
        elif isinstance(sendto, basestring):
            if len(self) == 1:
                for sub in self:
                    sendto = sub[sendto].subscribers
            else:
                raise
        elif not isinstance(sendto, (tuple, list, set)):
            sendto = (sendto, )

        for sub in sendto:
            sub.send(data)

    def packager(self, data):
        return json.dumps(data, separators=(',', ':'))

class Subscriber(object):
    def __init__(self, connect):
        self.connect = connect
        self.wrappers = dict()
        self.call()

    def __getitem__(self, key):
        return self.wrappers[key]

    def __contains__(self, key):
        return key in self.wrappers

    def get_obj(self, name):
        return self[name].obj

    def subscribe(self, data):
        wrapper = self._get_wrapper(data)
        group_name = wrapper.group_name
        if group_name in self:
            self.unsubscribe(group_name)

        wrapper.subscribe(self)
        self.wrappers[group_name] = wrapper

    def unsubscribe(self, data):
        wrapper = self._get_wrapper(data, True)
        group_name = wrapper.group_name
        self[group_name].unsubscribe(self)
        del self.wrappers[group_name]

    def _get_wrapper(self, data, unsub=False):
        if isinstance(data, basestring):
            if unsub:
                return self[data]
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
        for obj in self.wrappers.values():
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
        for wrapper in self.wrappers.values():
            if fun_name in wrapper.recvmeth_names:
                getattr(wrapper.obj, fun_name)(self, *attr)
                break
        else:
            print fun_name, attr
            raise

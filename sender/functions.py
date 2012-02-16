#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
from weakref import WeakValueDictionary

from public import get_wrapper
import base
import protocol

def set_base_params(cls, params):
    if params['name'] is None:
        params['name'] = cls.__name__

    params['recvmeth_name'] =_getmeths_names(cls,
        lambda atr: hasattr(atr, '_sender') and
        'recvmeth' in atr._sender)
    params['sendmeth_name'] =_getmeths_names(cls,
        lambda atr: hasattr(atr, '_sender') and
        'sendmeth' in atr._sender)

    init = cls.__dict__.get('init', lambda s: ())
    send_consructor_wrap(cls, init)
    send_destructor_wrap(cls)

def _getmeths_names(cls, filter_):
    names = []
    for atr_name in cls.__dict__.keys():
        atr = getattr(cls, atr_name)
        if filter_(atr):
            names.append(atr_name)
    return names

def getmeth_by_name(cls, names):
    for name in names:
        yield getattr(cls, name)

def initfunwrapper(cls, params):
    old_init = cls.__init__

    @wraps(old_init)
    def wrapper(self, *args, **kwargs):
        if get_wrapper(self, True) is None:
            params['Wrapper'](self, params['name'])
        old_init(self, *args, **kwargs)
    cls.__init__ = wrapper

def sendfunwrapper(cls, params):
    sendmeth = getmeth_by_name(cls, params['sendmeth_name'])
    for meth in sendmeth:
        _sendwrap(meth)

def _sendwrap(fn):
    @wraps(fn)
    def wrapper(self, to, *args, **kwargs):
        meth = getattr(self, fn.__name__)
        data = fn(self, *args, **kwargs)
        data = protocol.encode((meth, data))

        for sub in to:
            sub.send(data)
    setattr(fn.im_class, fn.__name__, wrapper)

def sendtofunwrapper(cls, params):
    sendmeth = getmeth_by_name(cls, params['sendmeth_name'])
    for meth in sendmeth:
        _sendtowrap(meth, params['Wrapper'])

def _sendtowrap(fn, wrappers):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        to = kwargs.pop('to', None)
        if to is None:
            to = set(get_wrapper(self))
        elif isinstance(to, base.Wrapper):
            to = set(to)
        elif isinstance(to, base.Subscriber):
            to = set((to,))
        else: raise

        if not to:
            return

        fn(self, to, *args, **kwargs)
    setattr(fn.im_class, fn.__name__, wrapper)

def receive(sub, data):
    fn, args = protocol.decode(sub, data)
    fn(sub, *args)

def recvfunwrapper(cls, params):
    recvmeth = getmeth_by_name(cls, params['recvmeth_name'])
    for meth in recvmeth:
        _recvwrap(meth)

def _recvwrap(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        return fn(self, *args, **kwargs)
    setattr(fn.im_class, fn.__name__, wrapper)

def send_consructor_wrap(cls, fn):
    @wraps(fn)
    def wrapper(self, to, *args, **kwargs):
        to.send(protocol.encode((type(self), (id(self), ))))
        data = fn(self, *args, **kwargs)
        to.send(protocol.encode((self, data)))
    setattr(cls, 'init', wrapper)

def send_destructor_wrap(cls):
    def destructor(self, to):
        meth = getattr(self, 'destructor')
        data = protocol.encode((meth, ()))

        to.send(data)
    destructor._sender = {'sendmeth': True,
                          'sendname': 'destructor'}
    setattr(cls, 'destructor', destructor)

def send_once(cls, params):
    sendmeth = getmeth_by_name(cls, params['sendmeth_name'])
    for meth in sendmeth:
        _send_once_wrap(meth)

def _send_once_wrap(fn):
    sendto = WeakValueDictionary()
    @wraps(fn)
    def wrapper(self, to, *args, **kwargs):
        cache_key = (id(self), args)
        if cache_key in sendto:
            if sendto[cache_key].status != 2:
                sendto[cache_key].status = 1
                sendto[cache_key].to.update(to)
                return
        call = lambda to: fn(self, to, *args, **kwargs)
        sendto[cache_key] = TimeoutSend(to, call)
    setattr(fn.im_class, fn.__name__, wrapper)

import gevent

class TimeoutSend(object):
    def __init__(self, to, call):
        self.to = to
        self.status = 1
        self.call = call
        self.greenlet = gevent.spawn(self.work)

    def work(self):
        while self.status:
            self.status = 0
            gevent.sleep(0.01)
        self.status = 2
        self.call(self.to)

base.wrapper_functions.extend((set_base_params, initfunwrapper,
                               recvfunwrapper, sendfunwrapper))

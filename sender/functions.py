#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps

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

def delfunwrapper(cls, params):
    old_del = getattr(cls, '__del__', lambda _: None)
    @wraps(old_del)
    def wrapper(self, *args, **kwargs):
        wr = get_wrapper(self, True)
        if wr is not None:
            wr.kill()
        old_del(self, *args, **kwargs)
    cls.__del__ = wrapper

def sendfunwrapper(cls, params):
    sendmeth = getmeth_by_name(cls, params['sendmeth_name'])
    for meth in sendmeth:
        _sendwrap(meth)

def _sendwrap(fn):
    @wraps(fn)
    def wrapper(self, to, *args, **kwargs):
        data = fn(self, *args, **kwargs)
        data = protocol.encode((self, fn, data))

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
            wr = get_wrapper(self)
            to = set(get_wrapper(id(self)))
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
        data = fn(self, *args, **kwargs)
        data = protocol.encode((self, type(self), data))

        to.send(data)
    setattr(cls, 'init', wrapper)

import gevent

def send_once(cls, params):
    sendmeth = getmeth_by_name(cls, params['sendmeth_name'])
    for meth in sendmeth:
        _send_once_wrap(meth)

def _send_once_wrap(fn):
    sendto = {}
    @wraps(fn)
    def wrapper(self, to, *args, **kwargs):
        cache_key = (id(self), args)
        if cache_key in sendto:
            if sendto[cache_key]['status'] != 2:
                sendto[cache_key]['status'] = 1
                sendto[cache_key]['to'].update(to)
                return

        def send_and_del(data):
            while data['status']:
                data['status'] = 0
                gevent.sleep(0.1)
            data['status'] = 2
            fn(self, data['to'], *args, **kwargs)
            if sendto[cache_key]['greenlet'] is gevent.getcurrent():
                del sendto[cache_key]
        data = {'status': 1,
                'to': to}
        data['greenlet'] = gevent.spawn(send_and_del, data)
        sendto[cache_key] = data
    setattr(fn.im_class, fn.__name__, wrapper)

base.wrapper_functions.extend((set_base_params, initfunwrapper,
    delfunwrapper, recvfunwrapper, sendfunwrapper))

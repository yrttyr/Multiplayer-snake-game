#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps

from public import get_wrapper

def set_base_params(cls, params):
    if params['name'] is None:
        params['name'] = cls.__name__

    params['recvmeth_name'] =_getmeths_names(cls,
        lambda atr: hasattr(atr, '_sender') and
        'recvmeth' in atr._sender)
    params['sendmeth_name'] =_getmeths_names(cls,
        lambda atr: hasattr(atr, '_sender') and
        'sendmeth' in atr._sender)

    if 'init' in cls.__dict__:
        init = cls.__dict__['init']
        params['sendmeth_name'].append('init')
        if not hasattr(init, '_sender'):
            init._sender = {
                'sendmeth': True,
                'sendname': 'init'
            }

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
        if fn._sender['sendname'] == 'init': #убрать этот костыль
            def get_data(_cache=[]):
                if not _cache:
                    #print self, args, kwargs
                    data = fn(self, *args, **kwargs)
                    _cache.append((self, type(self), data))
                return _cache[0]
        else:
            def get_data(_cache=[]):
                if not _cache:
                    data = fn(self, *args, **kwargs)
                    _cache.append((self, fn, data))
                return _cache[0]
        for sub in to:
            sub.send(get_data)

    setattr(fn.im_class, fn.__name__, wrapper)

def sendtofunwrapper(cls, params):
    sendmeth = getmeth_by_name(cls, params['sendmeth_name'])
    for meth in sendmeth:
        _sendtowrap(meth, params['Wrapper'])

def _sendtowrap(fn, wrappers):
    from sender.base import Wrapper, Subscriber
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        to = kwargs.pop('to', None)

        if to is None:
            wr = get_wrapper(self)
            to = set(get_wrapper(id(self)))
        elif isinstance(to, Wrapper):
            to = set(to)
        elif isinstance(to, Subscriber):
            to = set((to,))
        else: raise

        if not to:
            return

        fn(self, to, *args, **kwargs)
    setattr(fn.im_class, fn.__name__, wrapper)

def recvfunwrapper(cls, params):
    recvmeth = getmeth_by_name(cls, params['recvmeth_name'])
    for meth in recvmeth:
        _recvwrap(meth)

def _recvwrap(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        return fn(self, *args, **kwargs)
    setattr(fn.im_class, fn.__name__, wrapper)

import gevent

def send_once(cls, params):
    sendmeth = getmeth_by_name(cls, params['sendmeth_name'])
    for meth in sendmeth:
        _send_once_wrap(meth)

def _send_once_wrap(fn):
    sendto = {}
    @wraps(fn)
    def wrapper(self, to, *args, **kwargs):
        if args in sendto:
            if sendto[args]['status'] != 2:
                sendto[args]['status'] = 1
                sendto[args]['to'] = sendto[args]['to'].union(to)
                return

        def send_and_del(data):
            while data['status']:
                data['status'] = 0
                gevent.sleep(0.1)
            data['status'] = 2
            fn(self, data['to'], *args, **kwargs)
            if sendto[args]['greenlet'] is gevent.getcurrent():
                del sendto[args]
        data = {'status': 1,
                'to': to}
        data['greenlet'] = gevent.spawn(send_and_del, data)
        sendto[args] = data
    setattr(fn.im_class, fn.__name__, wrapper)


from base import wrapper_functions
wrapper_functions.extend((set_base_params, initfunwrapper, delfunwrapper,
    recvfunwrapper, sendfunwrapper))

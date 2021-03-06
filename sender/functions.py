#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
from weakref import WeakValueDictionary, ref

import protocol

def initfunwrapper(cls, params):
    from public import get_wrapper
    old_init = cls.__init__

    @wraps(old_init)
    def wrapper(self, *args, **kwargs):
        if params['Wrapper'] is not False:
            wr = get_wrapper(self, True)
            if wr is None or wr.obj is None:
                params['Wrapper'](self)
        old_init(self, *args, **kwargs)
    cls.__init__ = wrapper

def send_consructor_wrap(cls, params):
    fn = cls.__dict__.get('constructor', lambda s: ())
    @wraps(fn)
    def wrapper(self, to, *args, **kwargs):
        data = fn(self, *args, **kwargs)
        to.send(protocol.encode((type(self), (id(self), data))))
    setattr(cls, 'constructor', wrapper)

def send_destructor_wrap(cls, params):
    def destructor(self, to):
        meth = getattr(self, 'destructor')
        data = protocol.encode((meth, ()))
        to.send(data)
    destructor._sender = {'sendname': 'destructor', 'functions': ()}
    setattr(cls, 'destructor', destructor)

def sendfunwrapper(fn, params):
    @wraps(fn)
    def wrapper(self, to, *args, **kwargs):
        meth = getattr(self, fn.__name__)
        data = fn(self, *args, **kwargs)
        data = protocol.encode((meth, data))

        for sub in to:
            sub.send(data)
    return wrapper

def sendtofunwrapper(fn, params):
    import base
    from public import get_wrapper
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
    return wrapper

def send_once(fn, params):
    sendto = WeakValueDictionary()
    @wraps(fn)
    def wrapper(self, obj):
        cache_key = (id(self), id(obj))
        if cache_key in sendto:
            return

        sendto[cache_key] = TimeoutSend(self, fn, obj)
    return wrapper

import gevent

class TimeoutSend(object):
    def __init__(self, wrapped, fn, obj):
        self.wrapped = ref(wrapped)
        self.fn = fn
        self.obj = ref(obj)
        self.greenlet = gevent.spawn(self.work)

    def work(self):
        obj = self.obj()
        wrapped = self.wrapped()
        if obj is not None and wrapped is not None:
            from public import get_wrapper
            to = set(get_wrapper(wrapped))
            self.fn(wrapped, to, obj)

def receive(sub, data):
    try:
        fn, args = protocol.decode(sub, data)
    except:
         print 'Wrong data "%s"' % data
         return

    try:
        if fn._sender['recvmeth'] != True:
            raise AttributeError
    except (AttributeError, KeyError):
        print 'Wrong function "%s"' % fn.__name__
        return

    try:
        fn(sub, *args)
    except TypeError:
        print 'Wrong args %s' % args

def recvfunwrapper(fn, params):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        return fn(self, *args, **kwargs)
    return wrapper

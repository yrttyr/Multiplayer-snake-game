#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ('get_wrapper', 'get_wrapped')

def get_wrapper(key, silence=False):
    if not silence:
        return _get_wrapper(key)

    try:
        return _get_wrapper(key)
    except KeyError:
        return None

def _get_wrapper(key):
    if isinstance(key, int):
        return Wrapper._dict[key]
    if id(key) in Wrapper._dict:
        return Wrapper._dict[id(key)]

    if isinstance(key, basestring):
        return Wrapper._dict[key]
    return Wrapper._dict[type(key).__name__]

def get_wrapped(key):
    return get_wrapper(key).obj

import functions

base_fl = (functions.set_base_params, functions.initfunwrapper,
          functions.delfunwrapper, functions.sendfunwrapper,
          functions.recvfunwrapper)
standart_fl = base_fl + (functions.sendtofunwrapper, functions.attrs_replace)


from base import (Wrapper, WrapperSingleton,
                   WrapperUnique, Subscriber)

def send_cls(name=None, wrapper=Wrapper, funlist=standart_fl):
    params = {'Wrapper': wrapper,
              'name': name}
    def inner(cls):
        for fn in funlist:
            fn(cls, params)
        return cls
    return inner

def send_meth(name):
    def inner(meth):
        meth._sender = {
            'sendmeth': True,
            'sendname': name if name else meth.__name__
        }
        return meth
    return inner

def recv_meth(name=None):
    def inner(meth):
        meth._sender = {
            'recvmeth': True,
        }
        return meth
    return inner


import objects

objects.init()

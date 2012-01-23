#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from base import Wrapper, wrapper_functions

def send_cls(name=None, wrapper=Wrapper, funlist=wrapper_functions):
    params = {'Wrapper': wrapper,
              'name': name}
    def inner(cls):
        for fn in funlist:
            fn(cls, params)
        return cls
    return inner

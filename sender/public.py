#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functions

class_functions = [functions.initfunwrapper, functions.send_consructor_wrap,
                   functions.send_destructor_wrap]
recv_functions = [functions.recvfunwrapper]
send_functions = [functions.sendfunwrapper, functions.sendtofunwrapper]

def get_wrapper(key, silence=False):
    if not silence:
        return _get_wrapper(key)

    try:
        return _get_wrapper(key)
    except KeyError:
        return None

def _get_wrapper(key):
    if isinstance(key, (int, basestring)):
        return Wrapper._dict[key]
    if isinstance(key, Wrapper):
        return key

    try:
        return Wrapper._dict[id(key)]
    except: pass
    try:
        return Wrapper._dict[type(key).__name__]
    except: pass

    raise KeyError(key)

def get_wrapped(key):
    return get_wrapper(key).obj

def send_meth(name, functions=send_functions):
    def inner(meth):
        meth._sender = {
            'functions': functions,
            'sendname': name if name else meth.__name__
        }
        return meth
    return inner

def recv_meth(name=None, functions=recv_functions):
    def inner(meth):
        meth._sender = {
            'functions': functions,
            'recvmeth': True
        }
        return meth
    return inner

from base import Wrapper

def send_cls(wrapper=Wrapper, functions=class_functions):
    def inner(cls):
        params = {'Wrapper': wrapper}
        for fn in functions:
            fn(cls, params)

        for atr in cls.__dict__.values():
            if hasattr(atr, '_sender'):
                for fn in atr._sender['functions']:
                    atr = fn(atr, params)
                setattr(cls, atr.__name__, atr)
        return cls
    return inner

import objects
class_functions.append(objects.attrs_replace)

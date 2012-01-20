#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

def encode(data):
    return json.dumps(data, separators=(',', ':'),
                       default=obj_to_indef)

def obj_to_indef(obj):
    if type(obj) is type:
        return {'^class': obj.__name__}
    if hasattr(obj, 'im_func'): # is method?
        return {'^meth': obj._sender['sendname']}
    return {'^obj': id(obj)}

def decode(sub, data):
    print data
    data = data.decode("utf-8")
    data = json.loads(data, object_hook=get_parse(sub))

    obj, fun_name, args = data[0], data[1], data[2:]
    print fun_name, args
    meth = getattr(obj, fun_name)
    return meth, args

def get_parse(sub):
    def parse(dct):
        if '^obj' in dct:
            return sub[dct['^obj']]
        return dct
    return parse

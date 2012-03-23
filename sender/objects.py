#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import WeakValueDictionary, WeakKeyDictionary, ref
import UserDict

import public
import functions

send_functions = [functions.sendfunwrapper, functions.send_once]

@public.send_cls()
class SendObject(object):
    send_key = id
    def __init__(self, cls=None):
        def _change(obj, name, val, selfref=ref(self)):
            self = selfref()
            if self is not None:
                self.send(obj)
        self.change = _change

        self.send_keys = WeakKeyDictionary()
        if cls:
            auto_sub(cls, self)

    @public.send_meth('set')
    def send_create(self, obj):
        data = [getattr(obj, name, '') for name in obj.send_attrs]
        send_once = getattr(obj, 'send_once', ())
        data.extend(getattr(obj, name, '') for name in send_once)
        return self.send_keys[obj], data

    @public.send_meth('set', functions=send_functions)
    def send(self, obj):
        data = [getattr(obj, name, '') for name in obj.send_attrs]
        return self.send_keys[obj], data

    @public.send_meth('removeElement')
    def send_delete(self, key):
        return key,

    def subscribe_property(self, obj):
        send_key = getattr(obj, 'send_key', self.send_key)
        if callable(send_key):
            send_key = send_key(obj)
        self._test_same_key(send_key, obj)
        self.send_keys[obj] = send_key

        for name in getattr(obj, 'send_attrs', ()):
            property_ = getattr(type(obj), name)
            property_.subscribe(obj, self.change)

    def _test_same_key(self, send_key, obj):
        assert send_key not in self.send_keys.values(), \
            'тот же ключ %s' % send_key

    def unsubscribe_property(self, obj):
        for name in getattr(obj, 'send_attrs', ()):
            property_ = getattr(type(obj), name)
            property_.unsubscribe(obj)
        del self.send_keys[obj]

    def subscribe(self, sub):
        for obj in self:
            self.send_create(obj, to=sub)

@public.send_cls()
class SendList(set, SendObject):
    def __init__(self, cls=None):
        SendObject.__init__(self, cls)

    def add(self, obj):
        set.add(self, obj)
        self.subscribe_property(obj)
        self.send_create(obj)

    def remove(self, obj):
        key = self.send_keys[obj]
        self.unsubscribe_property(obj)
        set.remove(self, obj)
        self.send_delete(key)

@public.send_cls()
class SendDict(SendObject, UserDict.IterableUserDict):
    def __init__(self, cls=None):
        SendObject.__init__(self)
        UserDict.IterableUserDict.__init__(self)

    def __setitem__(self, key, obj):
        self.subscribe_property(obj)
        super(SendDict, self).__setitem__(key, obj)
        self.send_create(obj)

    def __delitem__(self, key):
        obj = self.data[key]
        self.unsubscribe_property(obj)
        del self.data[key]
        self.send_delete(key)

    def subscribe(self, sub):
        for obj in self.values():
            self.send_create(obj, to=sub)

    def _test_same_key(self, send_key, obj):
        if send_key in self:
            old_obj = self[send_key]
            self.unsubscribe_property(old_obj)

@public.send_cls()
class SendWeakDict(SendDict, WeakValueDictionary):
    def __init__(self):
        SendObject.__init__(self)
        WeakValueDictionary.__init__(self)
        def remove_wr(wr, selfref=ref(self)):
            self = selfref()
            if self is not None:
                del self[wr.key]
        self._remove = remove_wr

    def __delitem__(self, key):
        obj = self.data[key]()
        if obj is not None:
            self.unsubscribe_property(obj)
        del self.data[key]
        self.send_delete(key)

class Property(object):
    def __init__(self, name):
        self.name = '_%s' % name
        self.callback = WeakKeyDictionary()

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.name)

    def __set__(self, obj, value):
        setattr(obj, self.name, value)
        fn = self.callback.get(obj)
        if fn:
            fn()(obj, self.name, value)

    def __delete__(self, obj):
        delattr(obj, self.name)

    def subscribe(self, obj, callback):
        self.callback[obj] = ref(callback)

    def unsubscribe(self, obj):
        del self.callback[obj]

def auto_sub(cls, sendlist):
    old_init = cls.__init__
    def initfun(self, *args, **kwargs):
        sendlist.add(self)
        old_init(self, *args, **kwargs)
    cls.__init__ = initfun

def attrs_replace(cls, params):
    for name in getattr(cls, 'send_attrs', ()):
        setattr(cls, name, Property(name))

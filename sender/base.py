#!/usr/bin/env python
# -*- coding: utf-8 -*-

from weakref import WeakValueDictionary, ref

from public import get_wrapper
from functions import receive

class Link(object):
    keeper = set()

    def __init__(self):
        self.objs = set()
        self.keeper.add(self)

    def kill(self):
        for obj in set(self.objs):
            self.unsubscribe(obj)

        self.keeper.discard(self)

    def _subscribe(self, obj):
        self.objs.add(obj)

    def _unsubscribe(self, obj):
        self.objs.remove(obj)

    def __contains__(self, key):
        return key in self.objs

    def __len__(self):
        return len(self.objs)

    def __iter__(self):
        for i in self.objs:
            yield i

class Subscriber(Link):
    def __init__(self, connect):
        super(Subscriber, self).__init__()
        self._dict = WeakValueDictionary()
        self.connect = connect
        self.call()

    def subscribe(self, obj):
        wr = get_wrapper(obj)
        if wr not in self:
            self._subscribe(wr)
            wr._subscribe(self)
        return obj

    def unsubscribe(self, obj):
        obj = get_wrapper(obj)
        if obj in self:
            self._unsubscribe(obj)
            obj._unsubscribe(self)

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getitem__(self, key):
        return self._dict[key]

    def call(self):
        pass

    def send(self, data):
        try:
            self.connect.send(data)
        except EnvironmentError:
            self.kill()
            self.connect.close()

    def receive(self, data):
        receive(self, data)

class WrapperMeta(type):
    _dict = WeakValueDictionary()

    def __call__(cls, *args, **kwargs):
        instance = super(WrapperMeta, cls).__call__(*args, **kwargs)
        cls._dict[id(instance.obj)] = instance
        return instance

class Wrapper(Link):
    __metaclass__ = WrapperMeta

    def __init__(self, obj, group_name):
        super(Wrapper, self).__init__()
        self._obj = ref(obj, lambda wr: self.kill())
        self.keep_obj = None
        self.group_name = group_name

    @property
    def obj(self):
        return self._obj()

    def _subscribe(self, obj):
        super(Wrapper, self)._subscribe(obj)
        obj[id(self.obj)] = self.obj
        self.obj.constructor(to=obj)
        getattr(self.obj, 'subscribe', lambda _: None)(obj)

        if self.objs:
            self.keep_obj = self.obj

    def _unsubscribe(self, obj):
        super(Wrapper, self)._unsubscribe(obj)
        getattr(self.obj, 'unsubscribe', lambda _: None)(obj)
        self.obj.destructor(to=obj)

        if not self.objs:
            self.keep_obj = None

class WrapperSingletonMeta(WrapperMeta):
    def __call__(cls, wraped_class, *args, **kwargs):
        name = type(wraped_class).__name__
        if name in cls._dict:
            return cls._dict[name]
        sc = super(WrapperSingletonMeta, cls)
        instance = sc.__call__(wraped_class, *args, **kwargs)
        cls._dict[name] = instance
        return instance

class WrapperSingleton(Wrapper):
    __metaclass__ = WrapperSingletonMeta

    def _subscribe(self, obj):
        super(WrapperSingleton, self)._subscribe(obj)
        obj[type(self.obj).__name__] = self.obj

class WrapperUnique(Wrapper):
    def _subscribe(self, sub):
        name = type(self.obj).__name__
        if name in sub._dict:
            sub.unsubscribe(sub[name])
        super(WrapperUnique, self)._subscribe(sub)
        sub[name] = self.obj


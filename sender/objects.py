from weakref import WeakValueDictionary, WeakKeyDictionary, ref
from functools import partial
import UserDict

import public
import functions

send_functions = [functions.sendfunwrapper, functions.send_once]

@public.send_cls()
class SendObject(object):
    def __init__(self, cls=None):
        self.change = partial(self._change)
        if cls:
            auto_sub(cls, self)

    @public.send_meth('set')
    def send_create(self, obj):
         return id(obj), [getattr(obj, name, '')
                    for name in obj.send_attrs]

    @public.send_meth('set', functions=send_functions)
    def send(self, obj):
        return id(obj), [getattr(obj, name, '')
                    for name in obj.send_attrs]

    @public.send_meth('removeElement')
    def send_delete(self, obj):
        return id(obj),

    @public.recv_meth()
    def subscribe_to(self, sub, key):
        sub.subscribe(key)

    @public.recv_meth()
    def unsubscribe_to(self, sub, key):
        sub.unsubscribe(key)

    def subscribe_property(self, obj):
        for name in getattr(obj, 'send_attrs', ()):
            property_ = type(obj).__dict__[name]
            property_.subscribe(obj, self.change)
        self.send_create(obj)

    def _change(self, obj, name, val):
        self.send(obj)

    def subscribe(self, sub):
        for obj in self:
            self.send_create(obj, to=sub)

    def unsubscribe(self, sub):
        pass

@public.send_cls()
class SendList(set, SendObject):
    def __init__(self, cls=None):
        SendObject.__init__(self, cls)

    def add(self, obj):
        set.add(self, obj)
        self.subscribe_property(obj)

    def remove(self, obj):
        set.remove(self, obj)
        self.send_delete(obj)

@public.send_cls()
class SendDict(SendObject, UserDict.IterableUserDict):
    def __init__(self, cls=None):
        SendObject.__init__(self)
        UserDict.IterableUserDict.__init__(self)

    def get_send_key(self, obj):
        return getattr(obj, obj.send_attrs[0])

    def add(self, obj):
        key = self.get_send_key(obj)
        self[key] = obj
        self.subscribe_property(obj)

    def remove(self, obj):
        key = self.get_send_key(obj)
        del self.data[key]
        self.send_delete(key)

    @public.send_meth('set')
    def send_create(self, obj):
        return [getattr(obj, name, '')
                for name in obj.send_attrs]

    @public.send_meth('set', functions=send_functions)
    def send(self, obj):
        return [getattr(obj, name, '')
                for name in obj.send_attrs]

    @public.send_meth('removeElement')
    def send_delete(self, key):
        return key,

@public.send_cls()
class SendWeakDict(WeakValueDictionary, SendDict):
    def __init__(self):
        SendObject.__init__(self)
        WeakValueDictionary.__init__(self)
        def remove(wr, selfref=ref(self)):
            self = selfref()
            if self is not None:
                self.send_delete(wr.key)
                del self.data[wr.key]
        self._remove = remove

class Property(object):
    def __init__(self, name):
        self.name = '_%s' % name
        self.callback = WeakKeyDictionary()

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.name)

    def __set__(self, obj, value):
        setattr(obj, self.name, value)
        fn = self.callback.get(obj)
        if fn:
            fn(obj, self.name, value)

    def __delete__(self, obj):
        delattr(obj, self.name)

    def subscribe(self, obj, callback):
        self.callback[obj] = callback

def auto_sub(cls, sendlist):
    old_init = cls.__init__
    def initfun(self, *args, **kwargs):
        sendlist.add(self)
        old_init(self, *args, **kwargs)
    cls.__init__ = initfun

def attrs_replace(cls, params):
    for name in getattr(cls, 'send_attrs', ()):
        setattr(cls, name, Property(name))

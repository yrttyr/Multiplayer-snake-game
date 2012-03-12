from weakref import WeakValueDictionary, WeakKeyDictionary, ref
import UserDict

import public
import functions

send_functions = [functions.sendfunwrapper, functions.send_once]

@public.send_cls()
class SendObject(object):
    def __init__(self, cls=None):
        self.change = self._change
        if cls:
            auto_sub(cls, self)

    @public.send_meth('set')
    def send_create(self, obj):
         return self.get_senddata(obj)

    @public.send_meth('set', functions=send_functions)
    def send(self, obj):
        return self.get_senddata(obj)

    @public.send_meth('removeElement')
    def send_delete(self, key):
        return key,

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

@public.send_cls()
class SendList(set, SendObject):
    def __init__(self, cls=None):
        SendObject.__init__(self, cls)

    def add(self, obj):
        set.add(self, obj)
        self.subscribe_property(obj)

    def remove(self, obj):
        set.remove(self, obj)
        self.send_delete(id(obj))

    def get_senddata(self, obj):
        return id(obj), [getattr(obj, name, '')
                    for name in obj.send_attrs]

@public.send_cls()
class SendDict(SendObject, UserDict.IterableUserDict):
    def __init__(self, cls=None):
        SendObject.__init__(self)
        UserDict.IterableUserDict.__init__(self)

    def __setitem__(self, key, obj):
        super(SendDict, self).__setitem__(key, obj)
        self.subscribe_property(obj)

    def __delitem__(self, key):
        del self.data[key]
        self.send_delete(key)

    def get_senddata(self, obj):
        return [getattr(obj, name, '')
                for name in obj.send_attrs]

    def subscribe(self, sub):
        for obj in self.values():
            self.send_create(obj, to=sub)

@public.send_cls()
class SendWeakDict(SendDict, WeakValueDictionary):
    def __init__(self):
        SendObject.__init__(self)
        WeakValueDictionary.__init__(self)
        def remove(wr, selfref=ref(self)):
            self = selfref()
            if self is not None:
                del self[wr.key]
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

from weakref import WeakValueDictionary, ref
from functools import partial
import UserDict

import sender, public

class SendObject(object):
    def __init__(self, cls=None):
        self.change = partial(self._change)
        if cls:
            auto_sub(cls, self)

    @sender.send_meth('set')
    def send(self, obj):
        return id(obj), [getattr(obj, name, '')
                    for name in obj.send_attrs]

    @sender.send_meth('removeElement')
    def send_delete(self, obj):
        return id(obj),

    @sender.recv_meth()
    def subscribe_to(self, sub, key):
        sub.subscribe(key)

    @sender.recv_meth()
    def unsubscribe_to(self, sub, key):
        sub.unsubscribe(key)

    #@sender.recv_meth('del')
    #def delete(self, sub, obj):
        #print 'delete', obj
        #self.remove(obj)

    def subscribe_property(self, obj):
        for name in getattr(obj, 'send_attrs', ()):
            property_ = type(obj).__dict__[name]
            property_.subscribe(obj, self.change)
        self.send(obj)

    def _change(self, obj, name, val):
        self.send(obj)

    def subscribe(self, sub):
        for obj in self:
            self.send(obj, to=sub)

    def unsubscribe(self, sub):
        pass

class SendList(set, SendObject):
    def __init__(self, cls=None):
        SendObject.__init__(self, cls)

    def add(self, obj):
        set.add(self, obj)
        self.subscribe_property(obj)

    def remove(self, obj):
        set.remove(self, obj)
        self.send_delete(obj)

class SendDict(SendObject, UserDict.IterableUserDict):
    def __init__(self, cls=None):
        SendObject.__init__(self)
        UserDict.IterableUserDict.__init__(self)
        self.change = partial(self._change)

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

    @sender.send_meth('set')
    def send(self, obj):
        return [getattr(obj, name, '')
                for name in obj.send_attrs]

    @sender.send_meth('removeElement')
    def send_delete(self, key):
        return key,

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
        self.callback = WeakValueDictionary()

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.name)

    def __set__(self, obj, value):
        setattr(obj, self.name, value)
        fn = self.callback.get(id(obj))
        if fn:
            fn(obj, self.name, value)

    def __delete__(self, obj):
        delattr(obj, self.name)

    def subscribe(self, obj, callback):
        self.callback[id(obj)] = callback

def auto_sub(cls, sendlist):
    old_init = cls.__init__
    def initfun(self, *args, **kwargs):
        sendlist.add(self)
        old_init(self, *args, **kwargs)
    cls.__init__ = initfun

def attrs_replace(cls, params):
    for name in getattr(cls, 'send_attrs', ()):
        _attr_replace(cls, name)

def _attr_replace(cls, name):
    setattr(cls, name, Property(name))

import functions
from base import wrapper_functions

funlist = list(wrapper_functions) + [functions.send_once,
                                     functions.sendtofunwrapper]

SendObject = sender.send_cls(funlist=funlist)(SendObject)
SendList = sender.send_cls(funlist=funlist)(SendList)
SendDict = sender.send_cls(funlist=funlist)(SendDict)
SendWeakDict = sender.send_cls(funlist=funlist)(SendWeakDict)
wrapper_functions.extend((attrs_replace, functions.sendtofunwrapper))

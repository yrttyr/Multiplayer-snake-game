import sender
from weakref import WeakValueDictionary
from functools import partial

class SendList(set):
    def __init__(self, cls):
        self.change = partial(self._change)
        auto_sub(cls, self.change)

    @sender.send_meth('set')
    def send(self, obj):
        return id(obj), [getattr(obj, name, '')
                    for name in obj.send_attrs]

    @sender.send_meth('delRow')
    def send_delete(self, obj):
        return id(obj),

    @sender.recv_meth()
    def subscribe_to(self, sub, key):
        sub.subscribe(key)

    @sender.recv_meth()
    def unsubscribe_to(self, sub, key):
        sub.unsubscribe(key)

    @sender.recv_meth('del')
    def delete(self, sub, obj):
        print 'delete', obj
        self.remove(obj)

    def remove(self, obj):
        super(SendList, self).remove(obj)
        self.send_delete(obj)

    def _change(self, obj, name, val):
        self.send(obj)

    def init(self):
        return self.param_names,

    def subscribe(self, sub):
        for obj in self:
            self.send(obj, to=sub)

    def unsubscribe(self, sub):
        pass

class Attribute(object):
    def __init__(self, name):
        self.name = '_%s' % name
        self.callback = WeakValueDictionary()

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.name)

    def __set__(self, obj, value):
        setattr(obj, self.name, value)
        fn = self.callback.get(id(obj))
        fn(obj, self.name, value)

    def __delete__(self, obj):
        delattr(obj, self.name)

    def subscribe(self, obj, callback):
        self.callback[id(obj)] = callback

def auto_sub(cls, fn):
    old_init = cls.__init__
    def initfun(self, *args, **kwargs):
        for name in getattr(cls, 'send_attrs', ()):
            cls.__dict__[name].subscribe(self, fn)
        old_init(self, *args, **kwargs)
    cls.__init__ = initfun

def attrs_replace(cls, params):
    for name in getattr(cls, 'send_attrs', ()):
        _attr_replace(cls, name)

def _attr_replace(cls, name):
    setattr(cls, name, Attribute(name))

import functions
from base import wrapper_functions

funlist = list(wrapper_functions) + [functions.send_once,
                                     functions.sendtofunwrapper]

SendList = sender.send_cls(funlist=funlist)(SendList)
wrapper_functions.extend((attrs_replace, functions.sendtofunwrapper))

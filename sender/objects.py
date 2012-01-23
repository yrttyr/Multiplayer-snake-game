import sender

class SendList(set):
    def __init__(self, param_names):
        self.param_names = param_names

    @sender.send_meth('set')
    def send(self, obj):
        return id(obj), [getattr(obj, name, '')
                    for name in self.param_names]

    @sender.send_meth('delRow')
    def send_delete(self, obj):
        return id(obj),

    @sender.recv_meth()
    def subscribe_to(self, sub, indef):
        wrapped = sender.get_wrapped(indef)
        sub.subscribe(wrapped)

    @sender.recv_meth()
    def unsubscribe_to(self, sub, indef):
        wr = sender.Wrapper.get(indef)
        sub.unsubscribe(wr.obj)

    @sender.recv_meth('del')
    def delete(self, sub, obj):
        print 'delete', obj
        self.remove(obj)

    def remove(self, obj):
        super(SendList, self).remove(obj)
        self.send_delete(obj)

    def change(self, obj, name, val):
        self.send(obj)

    def init(self):
        return self.param_names,

    def subscribe(self, sub):
        for obj in self:
            self.send(obj, to=sub)

    def unsubscribe(self, sub):
        pass

import functions

def attrs_replace(cls, params):
    sendlist_instances = [value for value in cls.__dict__.values()
                          if isinstance(value, SendList)]

    if not sendlist_instances:
        return

    _attr_initwrap(cls, sendlist_instances)

    for sendlist in sendlist_instances:
        for name in sendlist.param_names:
            _attr_replace(cls, sendlist, name)

def _attr_initwrap(cls, sendobjs):
    old_init = cls.__init__
    def initfun(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        for obj in sendobjs:
            obj.add(self)
    cls.__init__ = initfun

def _attr_replace(cls, sendobj, name):
    hidden_name = '_%s' % name

    def getx(self):
        return getattr(self, hidden_name)

    def setx(self, val):
        setattr(self, hidden_name, val)
        sendobj.change(self, name, val)

    def delx(self):
        delattr(self, hidden_name)
        sendobj.change(self, name, None)

    setattr(cls, name, property(getx, setx, delx))

from base import wrapper_functions

funlist = list(wrapper_functions) + [functions.send_once,
                                     functions.sendtofunwrapper]

SendList = sender.send_cls(funlist=funlist)(SendList)
wrapper_functions.extend((attrs_replace, functions.sendtofunwrapper))

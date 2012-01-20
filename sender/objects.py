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

def init():
    global SendList
    from sender import functions, base_fl

    funlist = base_fl + (functions.send_once, functions.sendtofunwrapper)
    SendList = sender.send_cls(funlist=funlist)(SendList)


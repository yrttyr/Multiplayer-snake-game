#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path = ['../'] + sys.path

import unittest
import weakref

import sender


class TestSendto(unittest.TestCase):
    class Connect(object):
        def __init__(self):
            self.data = []

        def send(self, data):
            self.data.append(data)

    def setUp(self):
        reload(sender)

        @sender.send_cls()
        class C1(object):
            call_with_conn = ()

            @sender.send_meth('1_1')
            def data_1(self):
                return '1_1'

            @sender.send_meth('1_2')
            def data_2(self):
                return '1_2'
        self.C1 = C1

        @sender.send_cls()
        class C2(object):
            call_with_conn = ()

            @sender.send_meth('2_1')
            def data_1(self):
                return '2_1'

            @sender.send_meth('2_2')
            def data_2(self):
                return '2_2'
        self.C2 = C2

        self.c1 = C1()
        self.c2 = C2()
        self.connect1 = self.Connect()
        self.subscriber1 = sender.Subscriber(self.connect1)
        self.connect2 = self.Connect()
        self.subscriber2 = sender.Subscriber(self.connect2)

    def test_unname____(self):
        self.subscriber1.subscribe(self.c1)
        self.subscriber1.subscribe(self.c2)
        self.subscriber2.subscribe(self.c1)

        sub = self.subscriber1
        sender.sendto(sub, sub['C1'].subscribers,
                      'C1', 'data_1')

        sub = self.subscriber2
        sender.sendto(sub, [self.subscriber2],
                      'C1', 'data_2')

        self.assertEqual(self.connect1.data, [
                         '["1_1","1_1"]',
                         '["1_1","1_1"]'])
        self.assertEqual(self.connect2.data, [
                         '["1_2","1_2"]',])
class TestDelete(unittest.TestCase):

    def setUp(self):
        reload(sender)

        @sender.send_cls()
        class C(object):
            pass
        self.C = C

        self.c = self.C()
        self.weak_c = weakref.ref(self.c)

        self.subscriber = sender.Subscriber(None)
        self.subscriber.subscribe(self.c)
        self.weak_send_obj = weakref.ref(self.subscriber['C'])

    def test_del_obj(self):
        del self.c
        self.assertIsInstance(self.weak_c(), self.C)
        self.assertIsInstance(self.weak_send_obj(), sender.Wrapper)

    def test_unsub(self):
        self.subscriber.unsubscribe('C')
        self.assertIsInstance(self.weak_c(), self.C)
        self.assertIsInstance(self.weak_send_obj(), sender.Wrapper)

    def test_unsub_and_del_obj(self):
        self.subscriber.unsubscribe('C')
        del self.c
        self.assertIsNone(self.weak_c())
        self.assertIsNone(self.weak_send_obj())

    def test_del_obj_and_unsub(self):
        del self.c
        self.subscriber.unsubscribe('C')
        self.assertIsNone(self.weak_c())
        self.assertIsNone(self.weak_send_obj())

    def test_del_obj_and_link_and_unsub(self):
        del self.c
        link = self.weak_c()
        self.subscriber.unsubscribe('C')
        self.assertIsInstance(self.weak_c(), self.C)
        self.assertIsInstance(self.weak_send_obj(), sender.Wrapper)

class TestSend(unittest.TestCase):

    class Connect(object):
        def __init__(self):
            self.data = []

        def send(self, data):
            self.data.append(data)

    def setUp(self):
        reload(sender)

        @sender.send_cls()
        class C(object):
            call_with_conn = 'data_1', 'data_4'

            @sender.send_meth('test_send_1')
            def data_1(self):
                return 'info_1'

            @sender.send_meth('test_send_2')
            def data_2(self):
                return 'info_2'

            @sender.send_meth('test_send_3')
            def data_3(self):
                return 'info_3'

            @sender.send_meth('test_send_4')
            def data_4(self):
                return 'info_4'

        @sender.send_cls()
        class Cn(object):
            call_with_conn = ()

            @sender.send_meth('test_send_Cn')
            def send_data(self):
                return 'info_Cn'

        self.C = C
        self.c = self.C()
        self.Cn = Cn
        self.cn = self.Cn()

        self.connect1 = self.Connect()
        self.subscriber1 = sender.Subscriber(self.connect1)

        self.connect2 = self.Connect()
        self.subscriber2 = sender.Subscriber(self.connect2)

    def test_call_with_conn(self):
        self.subscriber1.subscribe(self.c)
        self.subscriber2.subscribe(self.c)

        self.assertEqual(self.connect1.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]'])
        self.assertEqual(self.connect2.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]'])

    def test_send(self):
        self.subscriber1.subscribe(self.c)
        self.c.data_2()

        self.subscriber2.subscribe(self.c)
        self.c.data_3()

        self.assertEqual(self.connect1.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]',
                         '["test_send_2","info_2"]',
                         '["test_send_3","info_3"]'])
        self.assertEqual(self.connect2.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]',
                         '["test_send_3","info_3"]'])

    def test_sendto(self):
        self.subscriber1.subscribe(self.c)
        self.subscriber2.subscribe(self.c)

        self.c.data_2(_send_to=self.connect1)
        self.c.data_1(_send_to=self.connect2)
        self.c.data_3(_send_to=[self.connect2, self.connect1])

        self.assertEqual(self.connect1.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]',
                         '["test_send_2","info_2"]',
                         '["test_send_3","info_3"]'])
        self.assertEqual(self.connect2.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]',
                         '["test_send_1","info_1"]',
                         '["test_send_3","info_3"]'])

    def test_sendto_by_groupname(self): # переимновать
        self.subscriber1.subscribe(self.c)
        self.subscriber2.subscribe(self.c)
        self.subscriber1.subscribe(self.cn)

        self.cn.send_data(_send_to='C')

        self.assertEqual(self.connect1.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]',
                         '["test_send_Cn","info_Cn"]'])
        self.assertEqual(self.connect2.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]',
                         '["test_send_Cn","info_Cn"]'])
        # придумать ошибку
        # self.assertRaises(KeyError, self.c.data_1(_send_to='C'))

class TestCreateWrapper(unittest.TestCase):
    def setUp(self):
        reload(sender)

    def test_noinit(self):
        class C(object):
            pass

        CW = sender.send_cls()(C)
        c = CW()

    def test_inheritance(self):
        count = [0]
        def call_count(obj):
            def inner(*args, **kwargs):
                count[0] += 1
                return obj(*args, **kwargs)
            return inner
        Wrapper = call_count(sender.Wrapper)
        sender.Wrapper = Wrapper

        @sender.send_cls()
        class P(object):
            pass

        @sender.send_cls()
        class C(P):
            pass

        c = C()
        self.assertEqual(count[0], 1)

    def test_singleton(self):
        @sender.send_cls()
        class C(object):
            pass
        c = C()
        self.assertNotIn('C', sender.wrappers)

        @sender.send_cls(singleton=True)
        class CS(object):
            pass
        cs = CS()
        self.assertIn('CS', sender.wrappers)

        @sender.send_cls('new_name', singleton=True)
        class CN(object):
            pass
        cn = CN()
        self.assertIn('new_name', sender.wrappers)
        self.assertNotIn('cn', sender.wrappers)

class TestSubscribeUnsubscribe(unittest.TestCase):
    def setUp(self):
        reload(sender)

        @sender.send_cls()
        class C(object):
            pass
        self.C = C

        self.c = self.C()
        self.weak_c = weakref.ref(self.c)
        self.weak_wrapper = weakref.ref(sender.wrappers[id(self.c)])

        self.subscriber = sender.Subscriber(None)

    def test_by_object(self):
        self.subscriber.subscribe(self.c)
        self.assertEqual(self.subscriber.get_obj('C'), self.c)
        self.subscriber.unsubscribe(self.c)
        self.assertRaises(KeyError, self.subscriber.get_obj, 'C')

    def test_by_wrapper(self):
        self.subscriber.subscribe(self.weak_wrapper())
        self.assertEqual(self.subscriber.get_obj('C'), self.c)
        self.subscriber.unsubscribe(self.weak_wrapper())
        self.assertRaises(KeyError, self.subscriber.get_obj, 'C')

    def test_by_object_id(self):
        self.subscriber.subscribe(id(self.c))
        self.assertEqual(self.subscriber.get_obj('C'), self.c)
        self.subscriber.unsubscribe(id(self.c))
        self.assertRaises(KeyError, self.subscriber.get_obj, 'C')

if __name__ == '__main__':
    unittest.main()

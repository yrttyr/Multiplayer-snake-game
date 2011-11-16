#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path = ['../'] + sys.path

import unittest
import weakref

import sender


class TestDelete(unittest.TestCase):

    def setUp(self):
        reload(sender)

        @sender.send_cls('Test', singleton=True)
        class C(object):
            pass
        self.C = C

        self.c = self.C()
        self.weak_c = weakref.ref(self.c)

        self.subscriber = sender.Subscriber(None)
        self.subscriber.subscribe(self.c)
        self.weak_send_obj = weakref.ref(self.subscriber.wrappers['Test'])

    def test_del_obj(self):
        del self.c
        self.assertIsInstance(self.weak_c(), self.C)
        self.assertIsInstance(self.weak_send_obj(), sender.Wrapper)

    def test_unsub(self):
        self.subscriber.unsubscribe('Test')
        self.assertIsInstance(self.weak_c(), self.C)
        self.assertIsInstance(self.weak_send_obj(), sender.Wrapper)

    def test_unsub_and_del_obj(self):
        self.subscriber.unsubscribe('Test')
        del self.c
        self.assertIsNone(self.weak_c())
        self.assertIsNone(self.weak_send_obj())

    def test_del_obj_and_unsub(self):
        del self.c
        self.subscriber.unsubscribe('Test')
        self.assertIsNone(self.weak_c())
        self.assertIsNone(self.weak_send_obj())

    def test_del_obj_and_link_and_unsub(self):
        del self.c
        link = self.weak_c()
        self.subscriber.unsubscribe('Test')
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

        @sender.send_cls('Test', singleton=True)
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
        self.C = C

    def test_call_with_conn(self):
        c = self.C()

        connect_1 = self.Connect()
        subscriber_1 = sender.Subscriber(connect_1)
        subscriber_1.subscribe(c)

        connect_2 = self.Connect()
        subscriber_2 = sender.Subscriber(connect_2)
        subscriber_2.subscribe(c)

        self.assertEqual(connect_1.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]'])
        self.assertEqual(connect_2.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]'])

    def test_send(self):
        c = self.C()

        connect_1 = self.Connect()
        subscriber_1 = sender.Subscriber(connect_1)
        subscriber_1.subscribe(c)
        c.data_2()

        connect_2 = self.Connect()
        subscriber_2 = sender.Subscriber(connect_2)
        subscriber_2.subscribe(c)
        c.data_3()

        self.assertEqual(connect_1.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]',
                         '["test_send_2","info_2"]',
                         '["test_send_3","info_3"]'])
        self.assertEqual(connect_2.data, [
                         '["test_send_1","info_1"]',
                         '["test_send_4","info_4"]',
                         '["test_send_3","info_3"]'])


class TestCreateWrapper(unittest.TestCase):
    def setUp(self):
        reload(sender)

    def test_noinit(self):
        class C(object):
            pass

        CW = sender.send_cls('Test')(C)
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

        @sender.send_cls('Parent')
        class P(object):
            pass

        @sender.send_cls('Child')
        class C(P):
            pass

        c = C()
        self.assertEqual(count[0], 1)

class TestSubscribeUnsubscribe(unittest.TestCase):
    def setUp(self):
        reload(sender)

        @sender.send_cls('Test', singleton=True)
        class C(object):
            pass
        self.C = C

        self.c = self.C()
        self.weak_c = weakref.ref(self.c)
        self.weak_wrapper = weakref.ref(sender.wrappers[id(self.c)])

        self.subscriber = sender.Subscriber(None)

    def test_by_object(self):
        self.subscriber.subscribe(self.c)
        self.assertEqual(self.subscriber.get_obj('Test'), self.c)
        self.subscriber.unsubscribe(self.c)
        self.assertRaises(KeyError, self.subscriber.get_obj, 'Test')

    def test_by_wrapper(self):
        self.subscriber.subscribe(self.weak_wrapper())
        self.assertEqual(self.subscriber.get_obj('Test'), self.c)
        self.subscriber.unsubscribe(self.weak_wrapper())
        self.assertRaises(KeyError, self.subscriber.get_obj, 'Test')

    def test_by_object_id(self):
        self.subscriber.subscribe(id(self.c))
        self.assertEqual(self.subscriber.get_obj('Test'), self.c)
        self.subscriber.unsubscribe(id(self.c))
        self.assertRaises(KeyError, self.subscriber.get_obj, 'Test')

if __name__ == '__main__':
    unittest.main()

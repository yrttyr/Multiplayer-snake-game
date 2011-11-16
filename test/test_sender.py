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
        self.sender = sender.sender

        @self.sender.send_cls('Test', singleton=True)
        class C(object):
            pass
        self.C = C

        self.c = self.C()
        self.weak_c = weakref.ref(self.c)

        self.subscriber = sender.Subscriber(None)
        self.subscriber.subscribe(self.sender['C'])
        self.weak_send_obj = weakref.ref(self.subscriber.send_obj['Test'])

    def test_del_obj(self):
        del self.c
        self.assertIsInstance(self.weak_c(), self.C)
        self.assertIsInstance(self.weak_send_obj(), sender.SendObj)

    def test_unsub(self):
        self.subscriber.unsubscribe('Test')
        self.assertIsInstance(self.weak_c(), self.C)
        self.assertIsInstance(self.weak_send_obj(), sender.SendObj)

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
        self.assertIsInstance(self.weak_send_obj(), sender.SendObj)


class TestSend(unittest.TestCase):

    class Connect(object):
        def __init__(self):
            self.data = []

        def send(self, data):
            self.data.append(data)

    def setUp(self):
        reload(sender)
        self.sender = sender.sender

        @self.sender.send_cls('Test', singleton=True)
        class C(object):
            call_with_conn = 'data_1', 'data_4'

            @self.sender.send_meth('test_send_1')
            def data_1(self):
                return 'info_1'

            @self.sender.send_meth('test_send_2')
            def data_2(self):
                return 'info_2'

            @self.sender.send_meth('test_send_3')
            def data_3(self):
                return 'info_3'

            @self.sender.send_meth('test_send_4')
            def data_4(self):
                return 'info_4'
        self.C = C

    def test_call_with_conn(self):
        c = self.C()

        connect_1 = self.Connect()
        subscriber_1 = sender.Subscriber(connect_1)
        subscriber_1.subscribe(self.sender['C'])

        connect_2 = self.Connect()
        subscriber_2 = sender.Subscriber(connect_2)
        subscriber_2.subscribe(self.sender['C'])

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
        subscriber_1.subscribe(self.sender['C'])
        c.data_2()

        connect_2 = self.Connect()
        subscriber_2 = sender.Subscriber(connect_2)
        subscriber_2.subscribe(self.sender['C'])
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
        self.sender = sender.sender

    def test_noinit(self):
        class C(object):
            pass

        CW = self.sender.send_cls('Test')(C)
        c = CW()

    def test_inheritance(self):
        count = [0]
        def call_count(obj):
            def inner(*args, **kwargs):
                count[0] += 1
                return obj(*args, **kwargs)
            return inner
        SendObj = call_count(sender.SendObj)
        sender.SendObj = SendObj

        @self.sender.send_cls('Parent')
        class P(object):
            pass

        @self.sender.send_cls('Child')
        class C(P):
            pass

        c = C()
        self.assertEqual(count[0], 1)

if __name__ == '__main__':
    unittest.main()

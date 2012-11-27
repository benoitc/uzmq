# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.
import time

import pyuv
import zmq
from zmq.tests import BaseZMQTestCase

from uzmq import ZMQ


def wait():
    time.sleep(.25)


class TestZMQStream(BaseZMQTestCase):

    def test_simple(self):
        req, rep = self.create_bound_pair(zmq.REQ, zmq.REP)
        wait()

        loop = pyuv.Loop.default_loop()
        s = ZMQ(loop, rep)

        r = []
        def cb(stream, msg, err):
            r.append(msg[0])

        s.start_read(cb)
        req.send(b'test')
        wait()

        def stop(handle):
            s.stop()

        t = pyuv.Timer(loop)
        t.start(stop, 0.8, 0.0)

        loop.run()
        assert r == [b'test']

    def test_echo(self):
        req, rep = self.create_bound_pair(zmq.REQ, zmq.REP)
        wait()

        loop = pyuv.Loop.default_loop()
        s = ZMQ(loop, rep)
        s1 = ZMQ(loop, req)

        r = []
        def cb(stream, msg, err):
            r.append(msg[0])
            stream.write(msg[0])

        r1 = []
        def cb1(stream, msg, err):
            r1.append(msg[0])
            s.stop()
            s1.stop()

        s.start_read(cb)
        s1.start_read(cb1)
        s1.write(b'echo')
        loop.run()

        assert r == [b'echo']
        assert r1 == [b'echo']



    def test_pubsub(self):
        pub, sub = self.create_bound_pair(zmq.PUB, zmq.SUB)
        sub.setsockopt(zmq.SUBSCRIBE,b'')
        wait()

        loop = pyuv.Loop.default_loop()
        s = ZMQ(loop, sub)
        s1 = ZMQ(loop, pub)

        r = []
        def cb(stream, msg, err):
            r.append(msg[0])
            s.stop()
            s1.stop()

        s.start_read(cb)
        s1.write(b"message")

        loop.run()
        assert r == [b'message']

    def test_pubsub_topic(self):
        pub, sub = self.create_bound_pair(zmq.PUB, zmq.SUB)
        sub.setsockopt(zmq.SUBSCRIBE,b'x')
        wait()

        loop = pyuv.Loop.default_loop()
        s = ZMQ(loop, sub)
        s1 = ZMQ(loop, pub)

        r = []
        def cb(stream, msg, err):
            r.append(msg[0])
            s.stop()
            s1.stop()

        s.start_read(cb)
        s1.write(b"message")
        s1.write(b"xmessage")


        loop.run()
        assert r == [b'xmessage']

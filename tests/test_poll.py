# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.

import pyuv
import zmq
from zmq.tests import BaseZMQTestCase

import time

from uzmq import ZMQPoll

def wait():
    time.sleep(.25)

class TestPoll(BaseZMQTestCase):

    def test_simple(self):
        """Tornado poller implementation maps events correctly"""
        req,rep = self.create_bound_pair(zmq.REQ, zmq.REP)

        loop = pyuv.Loop.default_loop()
        poll = ZMQPoll(loop, rep)

        r = []
        def cb(handle, ev, error):
            r.append(ev & pyuv.UV_READABLE)
            r.append(rep.recv())

        poll.start(pyuv.UV_READABLE, cb)
        req.send(b'req')
        t = pyuv.Timer(loop)

        def stop(h):
            poll.stop()

        t = pyuv.Timer(loop)
        t.start(stop, 0.4, 0.0)
        loop.run()

        assert r == [1, b'req']

    def test_poll_rw(self):
        """Tornado poller implementation maps events correctly"""
        req,rep = self.create_bound_pair(zmq.REQ, zmq.REP)
        wait()

        loop = pyuv.Loop.default_loop()
        poll = ZMQPoll(loop, rep)
        poll1 = ZMQPoll(loop, req)

        r = []
        def cb(handle, ev, error):
            r.append(ev & pyuv.UV_READABLE)
            r.append(rep.recv())
            handle.close()

        def cb1(handle, ev, error):

            r.append(ev & pyuv.UV_WRITABLE)
            req.send(b'req')
            handle.stop()

        poll.start(pyuv.UV_READABLE, cb)
        poll1.start(pyuv.UV_WRITABLE, cb1)

        t = pyuv.Timer(loop)

        def stop(h):
            poll.stop()
            poll1.close()

        loop.run()

        assert r == [2, 1, b'req']

    def test_echo(self):
        req, rep = self.create_bound_pair(zmq.REQ, zmq.REP)
        wait()

        loop = pyuv.Loop.default_loop()
        p = ZMQPoll(loop, rep)
        p1 = ZMQPoll(loop, req)

        r = []
        r1 = []

        def cb(handle, ev, error):
            if ev & pyuv.UV_READABLE:
                data = rep.recv()
                r.append(data)


            if ev & pyuv.UV_WRITABLE:
                rep.send(r[-1])
                if len(r) == 2:
                    handle.stop()



        def cb1(handle, ev, error):
            if ev & pyuv.UV_READABLE:
                data = req.recv()
                r1.append(data)

                if len(r1) == 2:
                    handle.stop()


            if ev & pyuv.UV_WRITABLE:
                req.send(b"echo")


        p.start(pyuv.UV_READABLE | pyuv.UV_WRITABLE, cb)
        p1.start(pyuv.UV_READABLE | pyuv.UV_WRITABLE, cb1)


        req.send(b"echo")

        def stop(h):
            p.close()
            p1.close()

        loop.run()

        assert r == [b'echo', b'echo']
        assert r1 == [b'echo', b'echo']

#-----------------------------------------------------------------------------
#  Copyright (c) 2010-2012 Brian Granger, Min Ragan-Kelley
#
#  This file is part of pyzmq
#
#  Distributed under the terms of the New BSD License.  The full license is in
#  the file COPYING.BSD, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import time
import os
import threading

import pyuv
import zmq
from zmq.tests import BaseZMQTestCase

from uzmq import ZMQPoll


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

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

        loop = pyuv.Loop.default_loop()
        poll = ZMQPoll(loop, rep)
        poll1 = ZMQPoll(loop, req)

        r = []
        def cb(handle, ev, error):
            r.append(ev & pyuv.UV_READABLE)
            r.append(rep.recv())

        def cb1(handle, ev, error):
            handle.stop()
            r.append(ev & pyuv.UV_WRITABLE)
            req.send(b'req')

        poll.start(pyuv.UV_READABLE, cb)
        poll1.start(pyuv.UV_WRITABLE, cb1)

        t = pyuv.Timer(loop)

        def stop(h):
            poll.stop()
            poll1.close()

        t = pyuv.Timer(loop)
        t.start(stop, 0.4, 0.0)
        loop.run()

        assert r == [2, 1, b'req']

    def test_multiple_write(self):
        """Tornado poller implementation maps events correctly"""
        req,rep = self.create_bound_pair(zmq.REQ, zmq.REP)

        loop = pyuv.Loop.default_loop()
        poll = ZMQPoll(loop, rep)
        poll1 = ZMQPoll(loop, req)

        r = []
        r1 = []
        r2 = []
        def cb(handle, ev, error):
            r.append(ev & pyuv.UV_READABLE)

            data = rep.recv()
            r.append(data)
            rep.send(data)
            if len(r1) == 2:
                handle.stop()


        def cb1(handle, ev, error):
            if ev & pyuv.UV_WRITABLE:
                r1.append(ev & pyuv.UV_WRITABLE)
                req.send(b'req')
            else:
                r2.append(req.recv())

            if len(r2) == 2:
                handle.stop()

        poll.start(pyuv.UV_READABLE, cb)
        poll1.start(pyuv.UV_READABLE | pyuv.UV_WRITABLE, cb1)

        loop.run()

        assert r == [1, b'req', 1, b'req']
        assert r1 == [2, 2]
        assert r2 == [b'req', b'req']

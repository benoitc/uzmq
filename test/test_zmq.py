# -*- coding: utf-8 -
#
# This file is part of gaffer. See the NOTICE for more information.
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

        def stop(handle):
            s.stop()

        t = pyuv.Timer(loop)
        t.start(stop, 0.2, 0.0)

        loop.run()

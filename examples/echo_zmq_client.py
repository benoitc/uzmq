# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.

import pyuv
import zmq
import uzmq


loop = pyuv.Loop.default_loop()

ctx = zmq.Context()
s = ctx.socket(zmq.REQ)
s.connect('tcp://127.0.0.1:5555')


def display(handle, msg, err):
    print(msg[0])

stream = uzmq.ZMQ(loop, s)
stream.start_read(display)

for i in range(10):
    stream.write("echo %s" % i)

loop.run()



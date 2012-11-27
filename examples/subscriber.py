# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.


import pyuv
import zmq
import uzmq

loop = pyuv.Loop.default_loop()

ctx = zmq.Context()
s = ctx.socket(zmq.SUB)
s.connect('tcp://127.0.0.1:5555')

s.setsockopt(zmq.SUBSCRIBE, b"")

stream = uzmq.ZMQ(loop, s)

def display(handle, msg, err):
    print(msg)

stream.start_read(display)
loop.run()

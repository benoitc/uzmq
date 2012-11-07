# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.

import pyuv
import zmq
import uzmq


loop = pyuv.Loop.default_loop()

ctx = zmq.Context()
s = ctx.socket(zmq.REP)
s.bind('tcp://127.0.0.1:5555')


stream = uzmq.ZMQ(loop, s)

def echo(handle, msg, err):
    print " ".join(msg)
    stream.send_multipart(msg)

stream.start_read(echo)

loop.run()

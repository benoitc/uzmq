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


def rep_handler(handle, events, errors):
    # We don't know how many recv's we can do?
    msg = s.recv()
    print(msg)
    # No guarantee that we can do the send. We need a way of putting the
    # send in the event loop.
    s.send(msg)


poll = uzmq.ZMQPoll(loop, s)
poll.start(pyuv.UV_READABLE, rep_handler)

loop.run()

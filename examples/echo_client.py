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


i = 1

def req_handler(handle, events, errors):
    global i
    if events &  pyuv.UV_WRITABLE:
        if i < 10:
            string = "echo %s" %i
            s.send(string.encode("utf8"))
            i += 1
        else:
            handle.stop()

    if events &  pyuv.UV_READABLE:
        msg = s.recv()
        print(msg)

poll = uzmq.ZMQPoll(loop, s)
poll.start(pyuv.UV_READABLE | pyuv.UV_WRITABLE, req_handler)


s.send(b"echo 0")


loop.run()

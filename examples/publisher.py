# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.

import time

import pyuv
import zmq
import uzmq

loop = pyuv.Loop.default_loop()

ctx = zmq.Context()
s = ctx.socket(zmq.PUB)
s.bind('tcp://127.0.0.1:5555')

stream = uzmq.ZMQ(loop, s)

print("waiting for subscriber to connect...")
# We need to sleep to allow the subscriber time to connect
time.sleep(1.0)
print("...done.")


print("start publishing")
for i in range(10):
    stream.write_multipart(str(i))
print("...done.")

loop.run()

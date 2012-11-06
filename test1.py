
from uzmq import ZMQPoll
import pyuv

req,rep = self.create_bound_pair(zmq.REQ, zmq.REP)

loop = pyuv.Loop.default_loop()
poll = ZMQPoll(loop, rep)
poll1 = ZMQPoll(loop, req)

r = []
r1 = []
def cb(handle, ev, error):
    r.append(ev & pyuv.UV_READABLE)

    data = rep.recv()
    r.append(data)
    rep.send(data)

    if len(r1) == 2:
        handle.stop()

def cb1(handle, ev, error):
    if len(r1) == 2:
        handle.stop()

    r1.append(ev & pyuv.UV_WRITABLE)
    req.send(b'req')

poll.start(pyuv.UV_READABLE, cb)
poll1.start(pyuv.UV_WRITABLE, cb1)

loop.run()

assert r == [1, b'req', 1, b'req']
assert r1 == [2, 2]

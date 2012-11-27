.. uzmq documentation master file, created by
   sphinx-quickstart on Wed Nov  7 00:32:37 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to uzmq's documentation!
================================

uzmq
====

libuv interface for ZeroMQ for your Python programs.

With uzmq you can use `zmq <http://zeromq.org>`_ sockets with the libuv
event loop binding proposed by the `pyuv library <http://pyuv.readthedocs.org>`_

.. image:: https://secure.travis-ci.org/benoitc/uzmq.png?branch=master
   :alt: Build Status
   :target: https://secure.travis-ci.org/benoitc/uzmq

Features
--------

- Simple interface to zeromq with the libuv event loop
- :doc:`poll`:  Poll handle
- :doc:`zmq`: ZMQ handle

.. note::
    uzmq source code is hosted on `Github <http://github.com/benoitc/uzmq.git>`_


Example of usage
----------------

Example of an echo server using a Poll handle::

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
        # No guarantee that we can do the send. We need a way of putting the
        # send in the event loop.
        s.send(msg)


    poll = uzmq.ZMQPoll(loop, s)
    poll.start(pyuv.UV_READABLE, rep_handler)

    loop.run()

The same but using a ZMQ handle::

    import pyuv
    import zmq
    import uzmq


    loop = pyuv.Loop.default_loop()

    ctx = zmq.Context()
    s = ctx.socket(zmq.REP)
    s.bind('tcp://127.0.0.1:5555')


    stream = uzmq.ZMQ(loop, s)

    def echo(handle, msg, err):
        print(msg[0])
        stream.write_multipart(msg)

    stream.start_read(echo)

    loop.run()

Contents:

.. toctree::
   :maxdepth: 4

   api
   news


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


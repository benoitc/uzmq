uzmq
====

libuv interface for ZeroMQ for your Python programs.

With uzmq you can use `zmq <http://zeromq.org>`_ sockets with the libuv
event loop binding proposed by the `pyuv library <http://pyuv.readthedocs.org>`_.

.. image:: https://secure.travis-ci.org/benoitc/uzmq.png?branch=master
   :alt: Build Status
   :target: https://secure.travis-ci.org/benoitc/uzmq

Features
--------

- Simple interface to zeromq with the libuv event loop
- Poll handle
- ZMQ handle

Documentation
-------------

http://uzmq.readthedocs.org

Installation
------------

uzmq requires Python superior to 2.6 (yes Python 3 is supported)

To install uzmq using pip you must make sure you have a
recent version of distribute installed::

    $ curl -O http://python-distribute.org/distribute_setup.py
    $ sudo python distribute_setup.py
    $ easy_install pip


To install from source, run the following command::

    $ git clone https://github.com/benoitc/uzmq.git
    $ cd uzmq && pip install -r requirements.txt


From pypi::

    $ pip install uzmq


License
-------

uzmq is available in the public domain (see UNLICENSE). gaffer is also
optionally available under the MIT License (see LICENSE), meant
especially for jurisdictions that do not recognize public domain
works.


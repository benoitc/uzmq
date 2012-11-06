# -*- coding: utf-8 -
#
# This file is part of zmq. See the NOTICE for more information.

from collections import deque
import logging

import pyuv
import six
import zmq

from .poll import ZMQPoll

class ZMQ(object):

    def __init__(self, loop, socket):
        self.loop = loop
        self.socket = socket
        self.active = False
        self.closed = True

        # shortcircuit some socket methods
        self.bind = self.socket.bind
        self.bind_to_random_port = self.socket.bind_to_random_port
        self.setsockopt = self.socket.setsockopt
        self.getsockopt = self.socket.getsockopt
        self.setsockopt_string = self.socket.setsockopt_string
        self.getsockopt_string = self.socket.getsockopt_string
        self.setsockopt_unicode = self.socket.setsockopt_unicode
        self.getsockopt_unicode = self.socket.getsockopt_unicode

        self._poll = ZMQPoll(loop, socket)
        self._events = 0

        self._send_queue = deque()
        self._read_cb = None
        self._read_copy = True

    def connect(self, addr, callback=None):
        self.socket.connect(addr)
        if six.callable(callback):
            callback(self)

    def start_read(self, callback, copy=True):
        """
        :param callback: callable
            callback must take exactly one argument, which will be a
            list, as returned by socket.recv_multipart()
            if callback is None, recv callbacks are disabled.
        :param copy: bool
            copy is passed directly to recv, so if copy is False,
            callback will receive Message objects. If copy is True,
            then callback will receive bytes/str objects.

        Start reading for incoming messages from the remote endpoint.
        """
        if not six.callable(callback):
            raise TypeError("a callable is required")

        if not self._events & pyuv.UV_READABLE:
            self._events |= pyuv.UV_READABLE
            self._poll.start(self._events, self._on_event)
        self._read_cb = callback
        self._read_copy = copy


    def stop_read(self):
        self._events = self._events & (~pyuv.UV_READABLE)
        self._poll.start(self._events, self._on_event)

    def write(self, msg, flags=0, copy=True, track=False,
            callback=None):
        return self.write_multipart([msg], flags=flags, copy=copy,
                track=track, callback=callback)

    def write_multipart(self, msg, flags=0, copy=True, track=False,
            callback=None):

        kwargs = dict(flags=flags, copy=copy, track=track)
        self._send_queue.put((msg, kwargs, callback))

        if not self._events & pyuv.UV_WRITABLE:
            self._events |= pyuv.UV_WRITABLE
            self._poll.start(self._events, self._on_event)

    def close(self):
        self._poll.close()

    def flush(self):
        if self._send_queue:
            while True:
                try:
                    self._send()
                except IndexError:
                    break

    def _send(self):
        (msg, kwargs, cb) = self._send_queue.popleft()
        try:
            status = self.socket.send_multipart(msg, **kwargs)
        except zmq.ZMQError as e:
            logging.error("SEND Error: %s", e)
            status = e

        if six.callable(cb):
            cb(self, msg, status)


    def _on_events(self, handle, events, err):
        if events & pyuv.UV_READABLE:
            self._on_read()

        if events & pyuv.UV_WRITEABLE:
            self._on_write()

    def _on_read(self):
        if self.closed or not self.active:
            return

        try:
            msg = self.socket.recv_multipart(zmq.NOBLOCK,
                    copy=self._read_copy)
        except zmq.ZMQError as e:
            if e.errno == zmq.EAGAIN:
                # state changed since poll event
                return
            else:
                logging.error("RECV Error: %s" % zmq.strerror(e.errno))
                self._read_cb(self, None, e.errno)
        else:
            self._read_cb(self, msg, None)

    def _on_write(self):
        try:
            self._send()
        except IndexError:
            pass

# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.

from collections import deque
import logging

import pyuv
import zmq

from .poll import ZMQPoll
from . import util

class ZMQ(object):
    """\
        :param loop: loop object where this handle runs (accessible
            through :py:attr:`Poll.loop`).
        :param int socket: zmq socket

        The ZMQ handles provides qsynchronous ZMQ sockets functionnality
        both for bound and connected sockets.
    """


    def __init__(self, loop, socket):
        self.loop = loop
        self.socket = socket

        # shortcircuit some socket methods
        self.bind = self.socket.bind
        self.bind_to_random_port = self.socket.bind_to_random_port
        self.connect = self.socket.connect
        self.setsockopt = self.socket.setsockopt
        self.getsockopt = self.socket.getsockopt
        self.setsockopt_string = self.socket.setsockopt_string
        self.getsockopt_string = self.socket.getsockopt_string
        self.setsockopt_unicode = self.socket.setsockopt_unicode
        self.getsockopt_unicode = self.socket.getsockopt_unicode

        self.fd = socket.getsockopt(zmq.FD)
        self._poll = pyuv.Poll(loop, self.fd)
        self._poll.start(pyuv.UV_READABLE, self._on_events)

        self._prepare_h = pyuv.Prepare(loop)
        self._waker = pyuv.Idle(self.loop)

        self._events = 0

        self._send_queue = deque()
        self._read_cb = None
        self._read_copy = True
        self._read_track = False


    def start_read(self, callback, copy=True, track=False):
        """
        :param callback: callable
            callback must take exactly one argument, which will be a
            /iist, as returned by socket.recv_multipart()
            if callback is None, recv callbacks are disabled.
        :param copy: bool
            copy is passed directly to recv, so if copy is False,
            callback will receive Message objects. If copy is True,
            then callback will receive bytes/str objects.
        :param track: bool
            Should the message be tracked for notification that ZMQ has
            finished with it? (ignored if copy=True)

        Callback signature: ``callback(zmq_handle, msg, error)``.

        Start reading for incoming messages from the remote endpoint.
        """
        if not util.is_callable(callback):
            raise TypeError("a callable is required")

        self._read_cb = callback
        self._read_copy = copy
        self._read_track = track

        self._prepare()

    def stop_read(self):
        """ Stop reading data from the remote endpoint. """
        self._events = self._events & (~pyuv.UV_READABLE)

    def write(self, msg, flags=0, copy=True, track=False,
            callback=None):
        """\
            :param msg: object, str, Frame The content of the message

            :param flags: int
                Any supported flag

            :param copy: bool
                Should the message be tracked for notification that ZMQ
                has finished with it? (ignored if copy=True)

            :param track: bool
                Should the message be tracked for notification that ZMQ
                has finished with it? (ignored if copy=True)


            Callback signature: ``callback(zmq_handle, msg, status)``.

                Send a message.  See zmq.socket.send for details."""
        return self.write_multipart([msg], flags=flags, copy=copy,
                track=track, callback=callback)

    def write_multipart(self, msg, flags=0, copy=True, track=False,
            callback=None):
        """ :param msg: object, str, Frame, the content of the message
            :param flags: int
                Any supported flag
            :param copy: bool
                Should the message be tracked for notification that ZMQ
                has finished with it? (ignored if copy=True)
            :param track: bool
                Should the message be tracked for notification that ZMQ
                has finished with it? (ignored if copy=True)

            Callback signature: ``callback(zmq_handle, msg, status)``.

            Send a multipart message. See zmq.socket.send_multipart for
            details."""

        # make sure we are sending bytes
        msg = [util.to_bytes(m) for m in msg]

        kwargs = dict(flags=flags, copy=copy, track=track)
        self._send_queue.append((msg, kwargs, callback))

    def stop(self):
        """ Stop the ZMQ handle """
        self._poll.stop()
        self._prepare_h.stop()
        self._waker.stop()

    def close(self):
        """Close the ZMQ handle. After a handle has been closed no other
        operations can be performed on it."""

        self._poll.close()
        self._prepare_h.close()
        self._waker.close()

    def flush(self):
        """Flush pending messages.

        This method safely handles all pending incoming and/or outgoing
        messages, bypassing the inner loop, passing them to the registered
        callbacks."""
        if self._send_queue:
            while True:
                try:
                    self._send()
                except IndexError:
                    break

    def _send(self):
        res = self._send_queue.popleft()
        msg, kwargs, cb = res
        kwargs['flags'] = zmq.NOBLOCK | kwargs['flags']
        try:
            status = self.socket.send_multipart(msg, **kwargs)
        except zmq.ZMQError as e:
            logging.error("SEND Error: %s", e)
            status = e

        if util.is_callable(cb):
            cb(self, msg, status)

    def _prepare_cb(self, handle):
        handle.stop()

        z_events = self.socket.getsockopt(zmq.EVENTS)

        if z_events & zmq.POLLIN:
            self._on_read()

        if z_events & zmq.POLLOUT:
            self._on_write()

    def _prepare(self):
        if self._prepare_h.active:
            return

        self._prepare_h.start(self._prepare_cb)
        self._waker.start(lambda h: h.stop())

    def _on_events(self, handle, events, err):
        z_events = self.socket.getsockopt(zmq.EVENTS)

        if z_events & zmq.POLLIN:
            self._on_read()

        if z_events & zmq.POLLOUT:
            self._on_write()

    def _on_read(self):
        if not self._poll.active:
            return

        try:
            msg = self.socket.recv_multipart(zmq.NOBLOCK,
                    copy=self._read_copy, track=self._read_track)
        except zmq.ZMQError as e:
            if e.errno == zmq.EAGAIN:
                # state changed since poll event
                return
            else:
                logging.error("RECV Error: %s" % zmq.strerror(e.errno))
                self._read_cb(self, None, e.errno)
        else:
            self._read_cb(self, msg, None)

        self._prepare()

    def _on_write(self):
        try:
            self._send()
        except IndexError:
            return

        self._prepare()

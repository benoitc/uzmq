# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.

"""
ZMQPoll: ZMQ Poll handle

"""
import pyuv
import zmq
from zmq.core.poll import Poller

from . import util

class ZMQPoll(object):
    """\
    :param loop: loop object where this handle runs (accessible
        through :py:attr:`Poll.loop`).
    :param int socket: zmq socket
        to be monitored for readibility or writability.

    ``ZMQPoll`` ZMQPoll handles can be used to monitor any ZMQ
    sockets for readability or writability.

    .. py:attribute:: loop

        *Read only*

        :py:class:`pyuv.Loop` object where this handle runs.

    """

    def __init__(self, loop, socket):
        self.loop = loop
        self.socket = socket

        # initialize private variable
        self._timer_h = pyuv.Timer(loop)
        self._poller = Poller()
        self._callback = None
        self._started = False

    @property
    def active(self):
        """*Read only*

            Indicates if this handle is active."""
        return self._timer_h.active

    @property
    def closed(self):
        """*Read only*

            Indicates if this handle is closing or already closed."""
        return self._timer_h.closed

    def start(self, events, callback, timeout=-1):
        """\
        :param events: int
            Mask of events that will be detected. The possible
            events are `pyuv.UV_READABLE` or `pyuv.UV_WRITABLE`.

        :param callback: callable
            Function that will be called when the ``Poll`` handle
            receives events.

        :param timeout: int
            Timeoout between each poll.

        Callback signature: ``callback(poll_handle, events, errorno)``.

        Start or update the event mask of the ``ZMQPoll`` handle.
        """
        if not util.is_callable(callback):
            raise TypeError("a callable is required")

        if timeout is None or timeout<0:
            timeout = 0.01

        self._callback = callback

        z_events = 0
        if events & pyuv.UV_READABLE:
            z_events |= zmq.POLLIN

        if events & pyuv.UV_WRITABLE:
            z_events |= zmq.POLLOUT


        if self._timer_h.active:
            self._timer.stop()
            self._poller.modify(self.socket, z_events)
        else:
            self._poller.register(self.socket, z_events)

        self._timer_h.start(self._on_timeout, timeout, timeout)


    def stop(self):
        """ Stop the ``Poll`` handle. """
        self._timer_h.stop()
        self._poller.unregister(self.socket)

    def close(self, callback=None):
        """
        :param callable callback: Function that will be called after the
            ``ZMQPoll`` handle is closed.

        Close the ``ZMQPoll`` handle. After a handle has been closed no other
        operations can be performed on it.
        """
        self._timer_h.close()
        self._poller.unregister(self.socket)

        if util.is_callable(callback):
            callback(self)

    def _on_timeout(self, handle):
        # trick to use the last state. Fix a race condition

        errno = 0
        z_events = self._poller.poll(0)
        if not z_events:
            return

        for fd, evt in z_events:
            events = 0
            if evt & zmq.POLLIN:
                events |= pyuv.UV_READABLE

            if evt & zmq.POLLOUT:
                events |= pyuv.UV_WRITABLE

            self._callback(self, events, errno)

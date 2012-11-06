# -*- coding: utf-8 -
#
# This file is part of gaffer. See the NOTICE for more information.

"""
ZMQPoll: ZMQ Poll handle

"""
import pyuv
import six
import zmq

class ZMQPoll(object):

    def __init__(self, loop, socket):
        """
        :param loop: loop object where this handle runs (accessible
        through :py:attr:`Poll.loop`).  :param int fd: File descriptor
        to be monitored for readibility or writability.

        ``ZMQPoll`` ZMQPoll handles can be used to monitor an arbitrary file
        descritor for readability or writability.  On Unix any file
        descriptor is supported but on Windows only sockets are
        supported.

        .. py:attribute:: loop

            *Read only*

            :py:class:`pyuv.Loop` object where this handle runs.

        .. py:attribute:: active

            *Read only*

            Indicates if this handle is active.

        .. py:attribute:: closed

            *Read only*

            Indicates if this handle is closing or already closed.

        """
        self.loop = loop
        self.socket = socket

        # initialize private variable
        self.fd = socket.getsockopt(zmq.FD)
        self._poller = pyuv.Poll(loop, self.fd)

        self._callback = None
        self._started = False

    @property
    def active(self):
        return self._poller.active

    @property
    def closed(self):
        return self._poller.closed

    def start(self, events, callback):
        """
        :param int events: Mask of events that will be detected. The
        possible events are `pyuv.UV_READABLE` or `pyuv.UV_WRITABLE`.

        :param callable callback: Function that will be called when the
        ``Poll`` handle receives events.

        Start or update the event mask of the ``ZMQPoll`` handle.

        Callback signature: ``callback(poll_handle, events,
        errorno)``.
        """
        if not six.callable(callback):
            raise TypeError("a callable is required")

        self._callback = callback
        self._poller.start(events, self._poll)

    def stop(self):
        """ Stop the ``Poll`` handle. """
        self._poller.stop()

    def close(self, callback=None):
        """
        :param callable callback: Function that will be called after the
            ``ZMQPoll`` handle is closed.

        Close the ``ZMQPoll`` handle. After a handle has been closed no other
        operations can be performed on it.
        """
        self._poller.close()
        if six.callable(callback):
            callback(self)

    def _poll(self, handle, evs, errno):
        # trick to use the last state. Fix a race condition
        z_events = self.socket.getsockopt(zmq.EVENTS)

        events = 0
        if z_events & zmq.POLLIN:
            events |= pyuv.UV_READABLE

        if z_events & zmq.POLLOUT:
            events |= pyuv.UV_WRITABLE

        if not events:
            self._callback(self, evs, errno)
        else:
            self._callback(self, events, errno)

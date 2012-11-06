# -*- coding: utf-8 -
#
# This file is part of gaffer. See the NOTICE for more information.

"""
ZMQPoll: ZMQ Poll handle

"""

import errno
import logging

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

        self.active = False
        self.closed = False

        # initialize private variable
        self._poller = zmq.Poller()
        self._prepare = pyuv.Prepare(loop)
        self._check = pyuv.Check(loop)
        self._waker = pyuv.Idle(loop)

        self._callback = None
        self._started = False



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

        assert self.active == False

        if not six.callable(callback):
            raise TypeError("a callable is required")

        self._callback = callback

        z_events = 0
        if events & pyuv.UV_READABLE:
            z_events |= zmq.POLLIN

        if events & pyuv.UV_WRITABLE:
            z_events |= zmq.POLLOUT

        if self._started:
            self._poller.modify(self.socket, z_events)
        else:
            self._poller.register(self.socket, z_events)
            self._prepare.start(self._poll)
            self._check.start(self._poll)
            self._waker.start(lambda x: None)
            self._waker.unref()
            self._started = True


    def stop(self):
        """ Stop the ``Poll`` handle. """
        self._check.stop()
        self._prepare.stop()
        self.active = False

    def close(self, callback=None):
        """
        :param callable callback: Function that will be called after the
            ``ZMQPoll`` handle is closed.

        Close the ``ZMQPoll`` handle. After a handle has been closed no other
        operations can be performed on it.
        """

        self.active = False
        self.closed = True
        self._poller.unregister(self.socket)
        self._check.close()
        self._prepare.close()
        self._waker.close()
        self._started = False
        if six.callable(callback):
            callback(self)

    def _poll(self, handle):
        try:
            results = self._poller.poll(100)
        except Exception as e:
            if (getattr(e, 'errno', None) == errno.EINTR or
                    (isinstance(getattr(e, 'args', None), tuple) and
                     len(e.args) == 2 and e.args[0] == errno.EINTR)):
                return
        except getattr(e, 'errno', None) == zmq.ETERM:
            self.close()
            self._callback(self, 0, e.errno)

        for fd, z_events in results:
            events = 0
            if z_events & zmq.POLLIN:
                events |= pyuv.UV_READABLE

            if z_events & zmq.POLLOUT:
                events |= pyuv.UV_WRITABLE

            try:
                self._callback(self, events, None)
            except (OSError, IOError) as e:
                if e.args[0] == errno.EPIPE:
                    # Happens when the client closes the connection
                    pass
                else:
                    logging.error("Exception in I/O handler for fd %s",
                                          fd, exc_info=True)

            except Exception:
                    logging.error("Exception in I/O handler for fd %s",
                                  fd, exc_info=True)

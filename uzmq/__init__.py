# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.

version_info = (0, 1, 0)
__version__ = ".".join(map(str, version_info))

from uzmq.poll import ZMQPoll
from uzmq.sock import ZMQ
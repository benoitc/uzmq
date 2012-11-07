# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.


try:
    is_callable = callable
except NameError:
    is_callable = lambda obj: hasattr(obj, '__call__')

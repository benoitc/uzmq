# -*- coding: utf-8 -
#
# This file is part of uzmq. See the NOTICE for more information.

import sys
import types

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

try:
    is_callable = callable
except NameError:
    is_callable = lambda obj: hasattr(obj, '__call__')

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str


def to_bytes(s):
    if isinstance(s, binary_type):
        return s
    return s.encode('utf8')

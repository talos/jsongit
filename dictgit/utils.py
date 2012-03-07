# -*- coding: utf-8 -*-

from time import altzone, daylight, timezone
from time import time as curtime
from pygit2 import Signature

"""
dictgit.utils
"""

def signature(name, email, time=None, offset=None):
    """Conveniently generate a pygit2.Signature.

    :param name: name for the signature
    :type name: string
    :param email: signature for the email
    :type email: string
    :param time:
        (optional) the time for the signature, in UTC seconds.  Defaults to
        current time.
    :type time: int
    :param offset:
        (optional) the time offset for the signature, in minutes.  Defaults to
        the system offset.
    :type offset: int

    :returns: a signature
    :rtype: pygit2.Signature
    """
    if not offset:
        offset = altzone / 60 if daylight else timezone / 60
    if not time:
        time = int(curtime())
    return Signature(name, email, time, offset)

# -*- coding: utf-8 -*-

import time

"""
dictgit.utils
"""

def signature(name, email, time=None, offset=None):
    """
    Convenience method to generate a pygit2.Signature.

    :param name: A String name
    :param email: A String email 
    """
    if not offset:
        offset = time.altzone / 60 if time.daylight else time.timezone / 60
    if not time
    return Signature(name, email, int(time.time()), offset)

# -*- coding: utf-8 -*-

"""
jsongit.author
"""

from time import altzone, daylight, timezone
from time import time as curtime
from pygit2 import Signature
import subprocess


class NoGlobalSetting(RuntimeError):

    def __init__(name):
        super("Git on this system has no global setting for %s" % name)


def global_config(name):
    """Find a git --global setting

    :param name: the name of the setting
    :type name: string
    :return: the value of the setting
    :rtype: string
    :raises: NoGlobalSetting
    """
    # TODO libgit2 provides an interface for this, but pygit2 does not.  Should
    # patch pygit2 to provide it.  In the interim, we must use subprocess.
    popen = subprocess.Popen(['git', 'config', '--global', name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    out, err = popen.communicate()
    if popen.returncode == 0:
        return out.rstrip()
    else:
        raise NoGlobalSetting(name)

def signature(name, email, time=None, offset=None):
    """Convenience method to generate pygit2 signatures.

    :param name: The name in the signature.
    :type name: string
    :param email: The email in the signature.
    :type email: string
    :param time: (optional) the time for the signature, in UTC seconds.
        Defaults to current time.
    :type time: int
    :param offset:
        (optional) the time offset for the signature, in minutes.
        Defaults to the system offset.
    :type offset: int

    :returns: a signature
    :rtype: pygit2.Signature
    """
    offset = offset or (altzone / 60 if daylight else timezone / 60)
    time = time or int(curtime())
    return Signature(name, email, time, offset)

# -*- coding: utf-8 -*-

"""
gitdict.signature
"""

from time import altzone, daylight, timezone
from time import time as curtime
from pygit2 import Signature

class DictAuthor(object):
    """Wrapper for a name and email to use when committing to git.

    :param name: The name to use when committing
    :type name: string
    :param email: The email to use when committing
    :type email: string
    """

    def __init__(self, name, email):
        self._name = name
        self._email = email

    @property
    def name(self):
        """The author's name.
        """
        return self._name

    @property
    def email(self):
        """The author's email.
        """
        return self._email

    def signature(self, time=None, offset=None):
        """Generate a pygit2.Signature.

        :param time:
            (optional) the time for the signature, in UTC seconds.  Defaults to
            current time.
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
        return Signature(self.name, self.email, time, offset)

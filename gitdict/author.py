# -*- coding: utf-8 -*-

"""
gitdict.author
"""

from .exceptions import NoGlobalAuthor
from time import altzone, daylight, timezone
from time import time as curtime
from pygit2 import Signature
import subprocess

def get_default_author():
    """Find the default author on this system.

    :returns:
        The default author as defined from git config --global user.name
        and git config --global user.email.
    :rtype: :class:`DictAuthor <DictAuthor>`

    :raises: :class:`NoGlobalAuthor <NoGlobalAuthor>`
    """
    # TODO libgit2 provides an interface for this, but pygit2 does not.  Should
    # patch pygit2 to provide it.  In the interim, we must use subprocess.
    try:
        git_args = ['git', 'config', '--global']
        name = subprocess.check_output(git_args + ['user.name']).rstrip()
        email = subprocess.check_output(git_args + ['user.email']).rstrip()
        return DictAuthor(name, email)
    except subprocess.CalledProcessError: # thankfully, error code is returned
        raise NoGlobalAuthor()

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

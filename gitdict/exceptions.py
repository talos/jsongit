# -*- coding: utf-8 -*-

"""
gitdict.exceptions
"""

class NoGlobalAuthor(StandardError):
    """Indication that the git on this system does not have a global value
    for user.name and user.email.  This can be rectified with:

    $ git config --global user.name 'My Name'
    $ git config --global user.email me@domain.com
    """
    pass

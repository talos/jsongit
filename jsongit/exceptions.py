# -*- coding: utf-8 -*-

"""
jsongit.exceptions
"""

class NotJsonError(ValueError):
    """
    Raised when an object that cannot be run through json.dumps is committed.
    Descends from ValueError.
    """
    pass


class BadKeyTypeError(TypeError):
    """
    Raised when a non-string is used as a key in a repository.  Descends from
    TypeError.
    """
    pass


class DifferentRepoError(ValueError):
    """This is raised if a merge is attempted on a :class:`JsonGitObject` in a
    different repo.
    """
    pass


class NoGlobalSettingError(RuntimeError):
    """Raised when the requested global setting does not exist.
    """

    def __init__(name):
        super("Git on this system has no global setting for %s" % name)



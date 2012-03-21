# -*- coding: utf-8 -*-

"""
jsongit.exceptions
"""

class NotJsonError(ValueError):
    """
    Raised when an object that cannot be run through :func:`json.dumps` is
    committed.  Subclasses :exc:`ValueError`.
    """
    pass


class InvalidKeyError(TypeError):
    """
    Raised when a non-string or invalid string is used as a key in a
    repository.  Subclasses :exc:`TypeError`.
    """
    pass


class DifferentRepoError(ValueError):
    """This is raised if a merge is attempted on a :class:`Object` in a
    different repo.  Subclasses :exc:`ValueError`.
    """
    pass


class NoGlobalSettingError(RuntimeError):
    """Raised when the requested global setting does not exist. Subclasses
    :exc:`RuntimeError`.
    """

    def __init__(self, name):
        super(NoGlobalSettingError, self).__init__(
            "Git on this system has no global setting '%s'" % name)

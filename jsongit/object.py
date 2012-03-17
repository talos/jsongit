# -*- coding: utf-8 -*-

"""
jsongit.object
"""

from collections import MutableMapping, MutableSequence

def dirty(meth):
    """Decorator that dirties up a JsonGitObject upon successful call.
    """
    def wrapped(self, *args, **kwargs):
        retval = meth(self, *args, **kwargs)
        self._dirty = True  # if above call fails, we're not dirtied.
        if self.autocommit:
            self.commit()
        return retval
    return wrapped


class JsonGitObject(MutableMapping, MutableSequence):

    def __init__(self, repo, key, autocommit):

        #: Whether changes should be automatically committed.
        self.autocommit = autocommit

        self._repo = repo
        self._key = key
        self._read()

    def _value_meth(self, meth):
        cls = self.value.__class__
        try:
            return getattr(cls, meth)
        except AttributeError:
            raise TypeError("%s does not support %s" % (cls, meth))

    def __contains__(self, item):
        return self._value_meth('__contains__')(self.value, item)

    def __len__(self):
        return self._value_meth('__len__')(self.value)

    def __iter__(self):
        return self._value_meth('__iter__')(self.value)

    def __getitem__(self, key):
        return self._value_meth('__getitem__')(self.value, key)

    @dirty
    def __setitem__(self, key, value):
        return self._value_meth('__setitem__')(self.value, key, value)

    @dirty
    def __delitem__(self, key):
        return self._value_meth('__delitem__')(self.value, key)

    @dirty
    def insert(self, item):
        return self._value_meth('insert')(self.value, item)

    def __repr__(self):
        return '%s(key=%s,value=%s,dirty=%s)' % (type(self).__name__,
                                                         self.key,
                                                         self._value.__repr__(),
                                                         self.dirty)

    def _read(self):
        head_id = self._repo._head_oid_for_key(self.key)
        self._value = self._repo._data_for_commit_oid(head_id)
        self._dirty = False

    @property
    def repo(self):
        """The :class:`JsonGitRepository` of this object.
        """
        return self._repo

    @property
    def key(self):
        """The String key for this dict in its repository.
        """
        return self._key

    @property
    def dirty(self):
        """Whether the current value is different than what's in the repo.
        """
        return self._dirty

    @property
    def value(self):
        """The current (possibly dirty) value of this object.
        """
        return self._value

    def commit(self, **kwargs):
        """Convenience wrapper for :func:`JsonGitRepository.commit`
        """
        self.repo.commit(self.key, self.value, **kwargs)
        self._dirty = False

    def merge(self, other, **kwargs):
        """Convenience wrapper for :func:`JsonGitRepository.commit`

        :param other: the object to merge in
        :type other: :class:`JsonGitObject`

        :raises: DifferentRepoError
        """
        if not isinstance(other, JsonGitObject):
            raise ValueError('Can only merge in another JsonGitObject')
        if other.repo == self.repo:
            if self.repo.merge(other.key, self.key, **kwargs):
                self._read()
                return True
            else:
                return False
        else:
            raise DifferentRepoError("Cannot merge object in, it's in another \
                                     repo")


class DifferentRepoError(ValueError):
    """This is raised if a merge is attempted on a :class:`JsonGitObject` in a
    different repo.
    """
    pass

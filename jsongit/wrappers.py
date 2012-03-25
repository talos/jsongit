# -*- coding: utf-8 -*-

"""
jsongit.wrappers

These classes provide limited interfaces to pygit2 and json_diff constructs.
"""

import json_diff
import itertools
import copy

class Commit(object):
    """A wrapper around :class:`pygit2.Commit` linking to a single key in the
    repo.
    """

    def __init__(self, repo, key, data, pygit2_commit):
        self._commit = pygit2_commit
        self._repo = repo
        self._key = key
        self._data = data

    def __eq__(self, other):
        return self.oid == other.oid

    def __str__(self):
        return "'%s'='%s'@%s" % (self.key, self.data, self.hex[0:10])

    def __repr__(self):
        return "%s(%s,message=%s,author=%s)" % (type(self).__name__,
                                              self.__str__(), self.message,
                                             self.author)

    @property
    def data(self):
        """
        :returns: the data associated with this commit.
        :rtype: Boolean, Number, None, String, Dict, or List
        """
        return self._data

    @property
    def key(self):
        """
        :returns: the key associated with this commit.
        :rtype: string
        """
        return self._key

    @property
    def oid(self):
        """
        :returns: The unique 20-byte ID of this Commit.
        :rtype: string
        """
        return self._commit.oid

    @property
    def hex(self):
        """
        :returns: The unique 40-character hex representation of this commit's ID.
        :rtype: string
        """
        return self._commit.hex

    @property
    def message(self):
        """
        :returns: The message associated with this commit.
        :rtype: string
        """
        return self._commit.message

    @property
    def author(self):
        """
        :returns: The author of this commit.
        :rtype: :class:`pygit2.Signature`
        """
        return self._commit.author

    @property
    def committer(self):
        """
        :returns: The committer of this commit.
        :rtype: :class:`pygit2.Signature`
        """
        return self._commit.committer

    @property
    def time(self):
        """
        :returns: The time of this commit.
        :rtype: long
        """
        return self._commit.commit_time

    @property
    def repo(self):
        """
        :returns: The repository of this commit.
        :rtype: :class:`Repository <jsongit.models.Repository>`
        """
        return self._repo


class DiffWrapper(object):
    """An internal wrapper for :mod:`json_diff`.
    """

    def __init__(self, diff):
        if Diff.is_json_diff(diff):
            # wrap recursive updates
            if Diff.UPDATE in diff:
                update = diff[Diff.UPDATE]
                for k, v in update.iteritems():
                    update[k] = DiffWrapper(v)
            self._replace = None
        else:
            self._replace = diff
            diff = {} if diff is None else diff

        self._diff = diff

    def __str__(self):
        return self._diff.__str__()

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self._diff.__repr__())

    def __getitem__(self, k):
        return self._diff[k]

    def __eq__(self, other):
        return self._diff == other

    @property
    def remove(self):
        """A dict of removed keys and their values.
        """
        return self._diff.get(Diff.REMOVE)

    @property
    def update(self):
        """A DiffWrapper
        """
        return self._diff.get(Diff.UPDATE)

    @property
    def append(self):
        """A dict of appended keys and their values.
        """
        return self._diff.get(Diff.APPEND)

    @property
    def replace(self):
        """The diff is simply to replace wholesale.
        """
        return self._replace

    def apply(self, original):
        """Return an object modified with the changes in this diff.

        :param original: the object to apply the diff to.
        :type original: list, dict, number, or string

        :returns: the modified object
        :rtype: list, dict, number, or string
        """
        if self.replace:
            return self.replace
        else:
            obj = copy.copy(original)
            for k, v in (self.remove or {}).iteritems():
                obj.pop(k)
            for k, v in (self.update or {}).iteritems():
                # Recursive application
                obj[k] = v.apply(obj[k])
            for k, v in (self.append or {}).iteritems():
                if hasattr(obj, 'insert'):
                    obj.insert(k, v)
                else:
                    obj[k] = v
            return obj


class Diff(DiffWrapper):
    """A class to encapsulate differences between two JSON git objects.
    """

    APPEND = '_append'
    REMOVE = '_remove'
    UPDATE = '_update'

    @classmethod
    def is_json_diff(cls, obj):
        """Determine whether a dict was produced by JSON diff.
        """
        if isinstance(obj, dict):
            return any(k in obj for k in [cls.APPEND, cls.REMOVE, cls.UPDATE])
        else:
            return False

    def __init__(self, obj1, obj2):
        if isinstance(obj2, obj1.__class__):
            c = json_diff.Comparator()
            c.obj1 = obj1
            c.obj2 = obj2
            diff = c._compare_elements(obj1, obj2)
            super(Diff, self).__init__(diff)
        else:
            # if types differ we just replace
            super(Diff, self).__init__(obj2)


class Conflict(object):
    """A class wrapper for the conflict between two diffs.
    """

    def __init__(self, diff1, diff2):
        self._conflict = {}
        if diff1.replace or diff2.replace:
            if diff1.replace != diff2.replace:
                self._conflict = {'replace': (diff1.replace, diff2.replace)}
        else:
            for verb1, verb2 in itertools.product(['append', 'update', 'remove'],
                                                    repeat=2):
                mod1 = getattr(diff1, verb1) or {}
                mod2 = getattr(diff2, verb2) or {}

                # Isolate simultaneously modified keys
                for k in (k for k in mod1 if k in mod2):
                    self._conflict.setdefault(verb1, {})
                    # If verbs were the same, it's OK unless mod was different.
                    if verb1 == verb2 and mod1[k] != mod2[k]:
                        self._conflict[verb1][k] = (mod1[k], mod2[k])
                    # Otherwise, it's a conflict no matter what
                    else:
                        self._conflict[verb1][k] = (mod1[k], None)
                        self._conflict.setdefault(verb2, {})
                        self._conflict[verb2][k] = (None, mod2[k])

    def __nonzero__(self):
        return len(self._conflict) != 0

    def __str__(self):
        return self._conflict.__str__()

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self._conflict.__repr__())

    @property
    def remove(self):
        """A dict of key removal conflict tuples.
        """
        return self._conflict.get('remove')

    @property
    def update(self):
        """A dict of key update conflict tuples.
        """
        return self._conflict.get('update')

    @property
    def append(self):
        """A dict of key append conflict tuples.
        """
        return self._conflict.get('append')

    @property
    def replace(self):
        """A tuple of the two diffs.
        """
        return self._conflict.get('replace')


class Merge(object):
    """A class wrapper for the results of a merge operation.
    """

    def __init__(self, success, original, merged, message, result=None,
                 conflict=None):
        self._success = success
        self._message = message
        self._original = original
        self._merged = merged
        self._conflict = conflict
        self._result = result

    def __str__(self):
        return self.message

    def __repr__(self):
        return "%s(success=%s,message=%s,conflict=%s,original=%s,merged=%s)" % (
            type(self).__name__, self.success, self.message, self.conflict,
            self.original, self.merged)

    def __nonzero__(self):
        return self.success

    @property
    def result(self):
        """
        :returns:
            the object resulting from this merge, or None if there was
            a conflict.
        """
        return self._result

    @property
    def success(self):
        """Whether the merge was a success.
        """
        return self._success

    @property
    def original(self):
        """The original object.
        """
        return self._original

    @property
    def merged(self):
        """The object that was merged in.
        """
        return self._merged

    @property
    def conflict(self):
        """The :class:`Conflict <jsongit.wrappers.Conflict>`, if the merge
        was not a success.
        """
        return self._conflict

    @property
    def message(self):
        """The message associated with this merge.
        """
        return self._message

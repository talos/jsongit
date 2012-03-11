# -*- coding: utf-8 -*-

"""
jsongit.object
"""

from collections import MutableMapping, MutableSequence
from .diff import JsonDiff


def dirty(meth):
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
        self._head_id = self._repo.get_commit_oid_for_key(self.key)
        self._value = self._repo.get_data_for_commit_oid(self._head_id)
        self._dirty = False

    def _immediate_ancestors_and_head(self):
        parent = self._head_id
        ancestors = []
        while parent:
            ancestors.append(parent)
            parents = self._repo.get_parent_oids_for_commit_oid(parent)
            if len(parents) == 1:
                parent = parents[0]
            else:
                break
        return ancestors

    @property
    def key(self):
        """The String key for this dict in its repository.
        """
        return self._key

    @property
    def dirty(self):
        """Whether this :class:`GitDict <GitDict>` has uncommitted changes.
        """
        return self._dirty

    @property
    def value(self):
        return self._value

    def commit(self, author=None, committer=None, message='', parents=None):
        """Commit the dict to its repository.

        :param author:
            (optional) The author of this commit. Defaults to global author.
        :type author: pygit2.Signature
        :param committer:
            (optional) The committer of this commit.  Will default to global
            author.
        :type committer: pygit2.Signature
        :param message:
            (optional) The commit message.  Defaults to a blank string.
        :type message: string
        :param parents:
            (optional) The 20-byte IDs of the parents of this commit.  Defaults
            to the last commit.
        :type parents: array
        """
        parents = [self._head_id] if parents == None else parents
        self._head_id = self._repo.raw_commit(self.key, self._value, author,
                                              committer, message, parents)
        self._dirty = False

    def merge(self, other, author=None, committer=None):
        """Try to merge another :class:`GitDict <GitDict>` into this one.
        If possible, will fast-forward the merged dict; otherwise, will attempt
        to merge in the intervening changes.

        :param other: the :class:`GitDict <GitDict>` to merge in.
        :type other: :class:`GitDict <GitDict>`
        :param author:
            (optional) The author of this commit, if one is necessary.
            Defaults to global author.
        :type author: pygit2.Signature
        :param committer:
            (optional) The committer of this commit, if one is necessary.
            Will default to global author.
        :type committer: pygit2.Signature
        :returns: True if the merge succeeded, False otherwise.
        :rtype: boolean
        """
        # No difference
        if self._head_id == other._head_id:
            return True

        # Test if a fast-forward is possible
        other_ancestors = other._immediate_ancestors_and_head()
        if self._head_id in other_ancestors:
            self._repo.fast_forward(self.key, other.key)
            self._read()
            return True

        # Do a merge if there were no overlapping changes
        # First, find the shared parent
        ancestors = self._immediate_ancestors_and_head()
        try:
            shared_ancestor_id = (v for v in ancestors if v in other_ancestors).next()
        except StopIteration:
            return False # todo warn there's no shared parent

        # Now, see if the diffs conflict
        # TODO: this breaks for non-dicts! bad bad bad
        shared_ancestor = self._repo.get_data_for_commit_oid(shared_ancestor_id)
        other_diff = JsonDiff(shared_ancestor, self._repo.get_data_for_commit_oid(other._head_id))
        self_diff = JsonDiff(shared_ancestor, self)

        conflict = self_diff.conflict(other_diff)

        # No-go, the user's gonna have to figure this one out
        if conflict:
            return False
        # Sweet. we can apply all the diffs.
        else:
            for k, v in other_diff.removed.items() + self_diff.removed.items():
                shared_ancestor.pop(k)
            for k, v in other_diff.updated.items() + self_diff.updated.items():
                shared_ancestor[k] = v
            for k, v in other_diff.appended.items() + self_diff.appended.items():
                shared_ancestor[k] = v
            self._value = shared_ancestor
            self.commit(author=author, committer=committer,
                        message='Auto-merge',
                        parents=[other._head_id, self._head_id])
            return True


# class GitDict(GitObject):
#     """The :class:`GitDict <GitDict>` object.  Functions just like a dict, but
#     it has a history and can be committed and merged.
# 
#     These should be created with a :class:`DictRepository <DictRepository>`
#     rather than instantiated directly.
#     """

# -*- coding: utf-8 -*-

"""
gitdict.dict
"""

from .diff import DictDiff

class GitDict(dict):
    """The :class:`GitDict <GitDict>` object.  Functions just like a dict, but
    it has a history and can be committed and merged.

    These should be created with a :class:`DictRepository <DictRepository>`
    rather than instantiated directly.
    """

    def __init__(self, repo, key, autocommit):

        #: Whether changes should be automatically committed.
        self.autocommit = autocommit

        self._repo = repo
        self._key = key
        self._dirty = False
        self._read()

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        self._dirty = True
        if self.autocommit:
            self.commit()

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(key=%s,dict=%s,dirty=%s)' % (type(self).__name__, self.key,
                                                dictrepr, self.dirty)

    def _read(self):
        self._head_id = self._repo.get_commit_oid_for_key(self.key)
        dict.clear(self)
        dict.update(self, self._repo.get_raw_dict_for_commit_oid(self._head_id))
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

    def update(self, *args, **kwargs):
        """Update as if this were a regular dict.
        """
        for k, v in dict(*args, **kwargs).iteritems():
            self[k] = v

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
        self._head_id = self._repo.raw_commit(self.key, self, author,
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
            self._repo.fast_forward(self, other)
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
        shared_ancestor = self._repo.get_raw_dict_for_commit_oid(shared_ancestor_id)
        other_diff = DictDiff(shared_ancestor, self._repo.get_raw_dict_for_commit_oid(other._head_id))
        self_diff = DictDiff(shared_ancestor, self)

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
            dict.clear(self)
            dict.update(self, shared_ancestor)
            self.commit(author=author, committer=committer,
                        message='Auto-merge',
                        parents=[other._head_id, self._head_id])
            return True


# -*- coding: utf-8 -*-

"""
dictgit.repository
"""

import os
import json_diff
try:
    import simplejson as json
    json; # appease the uncaring pyflakes god
except ImportError:
    import json
from pygit2 import init_repository, GIT_OBJ_BLOB, GIT_OBJ_TREE, Repository

# The name of the only blob within the tree.
DATA = 'data'

class DictRepository(object):
    """The :class:`DictRepository <DictRepository>` object.

    :param path:
        The path to the repository.  If the path does not exist, a new bare
        git repository will be initialized there.  If it does exist, then the
        directory will be used as a bare git repository.
    :type path: string
    """

    def __init__(self, path):
        if os.path.isdir(path):
            self.repo = Repository(path)
        else:
            self.repo = init_repository(path, True) # bare repo

    def _ref(self, path):
        """
        Returns the String ref that should point to the most recent commit for
        data of path.
        """
        return 'refs/%s/HEAD' % path

    def _last_commit(self, path):
        """
        Retrieve the last commit for `path`.

        Returns None if there is no last commit (it doesn't exist).
        """
        try:
            return self.repo[self.repo.lookup_reference(self._ref(path)).oid]
        except KeyError:
            return None

    def _dict(self, commit):
        """
        Returns the dict from a Commit. Returns None if no commit.
        """
        return json.loads(self.repo[commit.tree[DATA].oid].data) if commit else None

    def _commit_diff(self, commit1, commit2):
        """
        Returns the json_diff between the dicts of two arbitrary commits.
        """
        dict1, dict2 = self._dict(commit1), self._dict(commit2)

        return json_diff.Comparator().compare_dicts(dict1, dict2)

    def commit(self, key, data, author, message, committer=None, parents=None):
        """Commit a dict to this :class:`DictRepository <DictRepository>`.

        :param path: The key for the data.
        :type path: string
        :param data: The data.
        :type data: dict
        :param author: The author of the commit.
        :type author: pygit2.Signature
        :param message: The commit message.
        :type message: string
        :param committer:
            (optional) The committer of this commit.  Defaults to the author.
        :type committer: pygit2.Signature
        :param parents:
            (optional) A list of 20-byte object IDs of parent IDs.  Defaults
            to the ID of the last commit for the key, or an empty list if
            this is the first commit for the key.
        """
        if not isinstance(data, dict):
            raise ValueError('Cannot commit non-dict values.')

        committer = committer if committer else author

        blob_id = self.repo.write(GIT_OBJ_BLOB, json.dumps(data))

        # TreeBuilder doesn't support inserting into trees, so we roll our own
        tree_id = self.repo.write(GIT_OBJ_TREE, '100644 %s\x00%s' % (DATA, blob_id))

        # Default to last commit for this if no parents specified
        if not parents:
            last_commit = self._last_commit(key)
            parents = [last_commit.oid] if last_commit else []

        self.repo.create_commit(self._ref(key), author,
                                committer, message, tree_id, parents)

    def diff(self, key1, key2):
        """Compute a JSON diff between two dicts.

        :param key1: The key of the first dict.
        :type key1: string
        :param key2: The key of the second dict.
        :type key2: string

        :returns: The diff between the two dicts.
        :rtype: dict
        """
        return self._commit_diff(self._last_commit(key1),
                                 self._last_commit(key2))

    def merge(self, from_key, to_key, author, committer=None):
        """Try to merge two dicts.  If possible, will fast-forward the merged
        dict; otherwise, will attempt to merge in the intervening changes.

        :param from_key: the key of the dict to merge changes from.
        :type from_key: string
        :param to_key: the key of the dict to merge changes into.
        :type to_key: string
        :param author:
            the author of the commit resulting from this merge, if a new commit
            is necessary.
        :type author: pygit2.Signature
        :param committer:
            (optional) the committer of the commit resulting from this merge,
            if a new commit is necessary.  Defaults to author.
        :type committer: pygit2.Signature
        :returns: True if the merge succeeded, False otherwise.
        :rtype: boolean
        """
        from_commit = self._last_commit(from_key)
        to_commit = self._last_commit(to_key)

        committer = committer if committer else author

        # No difference
        if from_commit.oid == to_commit.oid:
            return True

        # Test if a fast-forward is possible
        parent = from_commit
        from_parents = []
        while parent:
            from_parents.append(parent)
            # No conflicting commits, fast forward this sucka by moving the ref
            if parent.oid == to_commit.oid:
                self.repo.lookup_reference(self._ref(to_key)).delete()
                self.repo.create_reference(self._ref(to_key), from_commit.oid)
                return True
            parent = parent.parents[0] if len(parent.parents) == 1 else None

        # Do a merge if there were no overlapping changes
        # First, find the shared parent
        shared_parent = None
        for from_parent in from_parents:
            parent = to_commit # start scanning up to_commit's ancestors
            while parent:
                if parent.oid == from_parent.oid:
                    shared_parent = parent
                    break
                parent = parent.parents[0] if len(parent.parents) == 1 else None
            if shared_parent:
                break
        if not shared_parent:
            return False # todo warn there's no shared parent

        # Now, see if the diffs conflict
        from_diff = self._commit_diff(shared_parent, from_commit)
        to_diff = self._commit_diff(shared_parent, to_commit)
        conflicts = {}
        for from_mod_type, from_mods in from_diff.items():
            for to_mod_type, to_mods in to_diff.items():
                for from_mod_key, from_mod_value in from_mods.items():
                    if from_mod_key in to_mods:
                        to_mod_value = to_mods[from_mod_key]
                        # if the mod type is the same, it's OK if the actual
                        # modification was the same.
                        if from_mod_type == to_mod_type:
                            if from_mod_value == to_mods[from_mod_key]:
                                pass
                            else:
                                conflicts[from_mod_key] = {
                                    'from': { from_mod_type: from_mod_value },
                                    'to'  : { to_mod_type: to_mod_value }
                                }
                        # if the mod type was not the same, it's a conflict no
                        # matter what
                        else:
                            conflicts[from_mod_key] = {
                                'from': { from_mod_type: from_mod_value },
                                'to'  : { to_mod_type: to_mod_value }
                            }

        # No-go, the user's gonna have to figure this one out
        if len(conflicts):
            return False
        # Sweet. we can apply all the diffs.
        else:
            merged = self._dict(shared_parent)
            for k, v in from_diff.get('_remove', {}).items() + \
                        to_diff.get('_remove', {}).items():
                merged.pop(k)
            for k, v in from_diff.get('_update', {}).items() + \
                        to_diff.get('_update', {}).items():
                merged[k] = v
            for k, v in from_diff.get('_append', {}).items() + \
                        to_diff.get('_append', {}).items():
                merged[k] = v
            self.commit(to_key, merged, author, 'Auto-merge',
                        committer=committer,
                        parents=[from_commit.oid, to_commit.oid])
            return True

    def clone(self, from_key, to_key):
        """Clone a dict.

        :param from_key: the key of the dict to clone
        :type from_key: string
        :param to_key: where to clone to
        :type to_key: string
        :raises:
            KeyError if from_key does not exist, ValueError if to_key already
            exists.
        """
        if self._last_commit(to_key):
            raise ValueError('Cannot clone to %s, there is already a dict there.' % to_key)
        elif self._last_commit(from_key):
            self.repo.create_reference(self._ref(to_key),
                                       self._last_commit(from_key).oid)
        else:
            raise KeyError('Cannot clone %s, there is no dict there.' % from_key)

    def get(self, key):
        """Retrieve the most recent dict.

        :param key: the dict's key
        :type key: string
        :returns: the most recent dict
        :rtype: dict
        """
        return self._dict(self._last_commit(key))

# -*- coding: utf-8 -*-

"""
jsongit.repository
"""

import os
try:
    import simplejson as json
    json; # appease the uncaring pyflakes god
except ImportError:
    import json
from pygit2 import init_repository, GIT_OBJ_BLOB, GIT_OBJ_TREE, Repository
from .object import JsonGitObject
from .diff import JsonDiff
from .utility import global_config, signature

# The name of the only blob within the tree.
DATA = 'data'

class JsonGitRepository(object):
    """
    The object must be initialized with a path or a repo.

    :param path:
        The path to a repository If it is a path that does not exist, a new
        bare git repository will be initialized there.  If it is a path that
        does exist, then the directory will be used as a bare git repository.
    :type path: string
    :param repo: An existing repository object.
    :type repo: :class:`pygit2.Repository`
    """

    def __init__(self, path=None, repo=None):
        self._global_name = global_config('user.name')
        self._global_email = global_config('user.email')
        if repo and path:
            raise TypeError("Cannot define repo and path")
        if repo:
            self._repo = repo
        elif path:
            if os.path.isdir(path):
                self._repo = Repository(path)
            else:
                self._repo = init_repository(path, True) # bare repo
        else:
            raise TypeError("Missing repo or path")

    def _key_to_ref(self, key):
        if isinstance(key, basestring):
            return 'refs/%s/HEAD' % key
        else:
            raise BadKeyTypeError("%s must be a string to be a key." % key)

    def _head_oid_for_key(self, key):
        return self._repo[self._repo.lookup_reference(self._key_to_ref(key)).oid].oid

    def _data_for_commit_oid(self, commit_oid):
        return json.loads(self._repo[self._repo[commit_oid].tree[DATA].oid].data)

    def _parent_oids_for_commit_oid(self, commit_oid):
        return [parent.oid for parent in self._repo[commit_oid].parents]

    def _immediate_ancestors_and_head(self, key):
        head_oid = self._head_oid_for_key(key)
        ancestors = []
        while head_oid:
            ancestors.append(head_oid)
            parents = self._parent_oids_for_commit_oid(head_oid)
            if len(parents) == 1:
                head_oid = parents[0]
            else:
                break
        return ancestors

    def _raw_commit(self, key, data, message, parents, **kwargs):
        """
        :return: The oid of the new commit.
        :rtype: 20 bytes

        :raises: NotJsonError, BadKeyTypeError
        """
        author = kwargs.pop('author', signature(self._global_name, self._global_email))
        committer = kwargs.pop('committer', author)
        if kwargs:
            raise TypeError("Unknown keyword args %s" % kwargs)
        try:
            blob_id = self._repo.write(GIT_OBJ_BLOB, json.dumps(data))
        except ValueError as e:
            raise NotJsonError(e)

        # TreeBuilder doesn't support inserting into trees, so we roll our own
        tree_id = self._repo.write(GIT_OBJ_TREE, '100644 %s\x00%s' % (DATA, blob_id))

        return self._repo.create_commit(self._key_to_ref(key), author,
                                        committer, message, tree_id, parents)

    def commit(self, key, data, autocommit=False, **kwargs):
        """Commit new data to the key.  Maintains relation to parent commits.

        :param key: The key of the new data.
        :type key: string
        :param data:  The value of the item.
        :type data: anything that runs through :func:`json.dumps`
        :param autocommit:
            whether the retrieved :class:`JsonGitObject` should autocommit.
        :type autocommit: boolean
        :param author:
            (optional) The signature for the author of the first commit.
            Defaults to global author.
        :param message:
            (optional) Message for first commit.  Defaults to "first commit" if
            there was no prior value.
        :type message: string
        :param author:
            (optional) The signature for the committer of the first commit.
            Defaults to global author.
        :type author: pygit2.Signature
        :param committer:
            (optional) The signature for the committer of the first commit.
            Defaults to author.
        :type author: pygit2.Signature

        :returns: the committed data, extended with JsonGit methods
        :rtype: :class:`JsonGitObject`

        :raises: NotJsonError, BadKeyTypeError
        """
        message = kwargs.pop('message', '' if self.has(key) else 'first commit')
        parents = kwargs.pop('parents', [self._head_oid_for_key(key)] if self.has(key) else [])
        self._raw_commit(key, data, message, parents, **kwargs)
        return self.get(key, autocommit=autocommit)

    def has(self, key):
        """Determine whether there is an entry for key in this repository.

        :param key: The key to check
        :type key: string

        :returns: whether there is an entry
        :rtype: boolean

        :raises: BadKeyTypeError
        """
        try:
            self._repo.lookup_reference(self._key_to_ref(key))
            return True
        except KeyError:
            return False

    def get(self, key, autocommit=False, **kwargs):
        """Obtain the data for a key.

        :param key: The key to look up.
        :type key: string
        :param autocommit:
            (optional) Whether the retrieved data should commit when changed.
            Defaults to false.
        :type autocommit: boolean
        :param default:
            (optional) A default value to return if the key does not exist.
        :type default: object

        :returns: the wrapped data
        :rtype: :class:`JsonGitObject`
        :raises: KeyError if there is no entry for key
        """
        if 'default' in kwargs:
            try:
                return JsonGitObject(self, key, autocommit=autocommit)
            except KeyError:
                return kwargs['default']
        else:
            return JsonGitObject(self, key, autocommit=autocommit)

    def fast_forward(self, source, dest, autocommit=False):
        """Fast forward the data at dest.  Loses intervening commits if there
        were any.

        :param source: the key of the source data
        :type source: string
        :param dest: the key of the destination data
        :type dest: string
        :param autocommit:
            (optional) Whether the retrieved data should commit when changed.
            Defaults to false.
        :type autocommit: boolean

        :returns: the wrapped data at dest
        :rtype: :class:`JsonGitObject`
        :raises: KeyError, BadKeyTypeError
        """
        if source == dest:
            raise ValueError()
        dest_ref = self._key_to_ref(dest)
        if self.has(dest):
            self._repo.lookup_reference(dest_ref).delete()
        self._repo.create_reference(dest_ref, self._head_oid_for_key(source))

        return self.get(dest, autocommit=autocommit)

    def merge(self, source, dest, **kwargs):
        """Try to merge two keys together.  If possible, will fast-forward,
        otherwise, will try to merge in the intervening changes.

        :param source: The key to merge from
        :type source: string
        :param dest: The key to merge into
        :type dest: string
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
        source_head, dest_head = [self._head_oid_for_key(k) for k in [source, dest]]
        # No difference
        if source_head == dest_head:
            return True

        # Test if a fast-forward is possible
        source_ancestors = self._immediate_ancestors_and_head(source)
        if dest_head in source_ancestors:
            self.fast_forward(source, dest)
            return True

        # Do a merge if there were no overlapping changes
        # First, find the shared parent
        dest_ancestors = self._immediate_ancestors_and_head(dest)
        try:
            shared_ancestor_id = (v for v in dest_ancestors if v in source_ancestors).next()
        except StopIteration:
            return False # todo warn there's no shared parent

        # Now, see if the diffs conflict
        # TODO: this breaks for non-dicts! bad bad bad
        shared_ancestor = self._data_for_commit_oid(shared_ancestor_id)
        other_diff = JsonDiff(shared_ancestor, self._data_for_commit_oid(dest_head))
        self_diff = JsonDiff(shared_ancestor, self._data_for_commit_oid(source_head))

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
            self._raw_commit(dest, shared_ancestor, 'Auto-merge',
                             [source_head, dest_head], **kwargs)
            return True

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



# -*- coding: utf-8 -*-

"""
jsongit.repository
"""

import os
from .object import JsonGitObject
from .signature import global_config, signature
try:
    import simplejson as json
    json; # appease the uncaring pyflakes god
except ImportError:
    import json
from pygit2 import init_repository, GIT_OBJ_BLOB, GIT_OBJ_TREE, Repository, GitError

# The name of the only blob within the tree.
DATA = 'data'

class JsonGitRepository(object):
    """The :class:`DictRepository <DictRepository>` object.

    :param repo_or_path:
        The path to a repository, or an existing pygit2.Repository object.
        If it is a path that does not exist, a new bare git repository will
        be initialized there.  If it is a path that does exist, then the
        directory will be used as a bare git repository.
    :type repo_or_path: string or pygit2.Repository
    """

    def __init__(self, repo_or_path=None):

        self._global_name = global_config('user.name')
        self._global_email = global_config('user.email')
        if isinstance(repo_or_path, Repository):
            self._repo = repo_or_path
        elif os.path.isdir(repo_or_path):
            self._repo = Repository(repo_or_path)
        else:
            self._repo = init_repository(repo_or_path, True) # bare repo

    def _key_to_ref(self, key):
        return 'refs/%s/HEAD' % key

    def get_commit_oid_for_key(self, key):
        return self._repo[self._repo.lookup_reference(self._key_to_ref(key)).oid].oid

    def get_data_for_commit_oid(self, commit_oid):
        return json.loads(self._repo[self._repo[commit_oid].tree[DATA].oid].data)

    def get_parent_oids_for_commit_oid(self, commit_oid):
        return [parent.oid for parent in self._repo[commit_oid].parents]

    def raw_commit(self, key, data, author, committer, message, parents):
        """Commit a dict to this :class:`DictRepository <DictRepository>`.
        It is recommended that you use the :class:`jsongit <jsongit>` commit
        method instead.

        :param data: the data to commit.
        :type data: anything json-serializable
        :param author:
            The author of the commit.  If None, will be replaced with default.
        :type author: pygit2.Signature
        :param committer:
            The committer of this commit. If None, will be replaced with author.
        :type committer: pygit2.Signature
        :param message: The commit message.
        :type message: string
        :param parents:
            A list of 20-byte object IDs of parent commits.  An empty list
            means this is the first commit.

        :return: The oid of the new commit.
        :rtype: 20 bytes
        """
        author = author or signature(self._global_name, self._global_email)
        committer = committer or author

        blob_id = self._repo.write(GIT_OBJ_BLOB, json.dumps(data))

        # TreeBuilder doesn't support inserting into trees, so we roll our own
        tree_id = self._repo.write(GIT_OBJ_TREE, '100644 %s\x00%s' % (DATA, blob_id))

        return self._repo.create_commit(self._key_to_ref(key), author,
                                        committer, message, tree_id, parents)

    def commit(self, key, data, author=None, committer=None, message='', parents=None):
        """Commit new data to the key.  Maintains relation to parent commits.
        """
        if not parents:
            parents = [self.get_commit_oid_for_key(key)] if self.has(key) else []
        self.raw_commit(key, data, author, committer, message, parents)

    def create(self, key, data, autocommit=False, message="first commit",
               author=None, committer=None):
        """Create a new :class:`jsongit <jsongit>` Wipes relation to any parent
        commits for key.

        :param key: The key of the new :class:`jsongit <jsongit>`
        :type key: :class:`jsongit <jsongit>`
        :param data:  The value of the item.
        :type data: anything serializable into JSON
        :param autocommit:
            (optional) Whether the :class:`jsongit <jsongit>` should
            automatically commit. Defaults to false.
        :type autocommit: boolean
        :param message:
            (optional) Message for first commit.  Defaults to "first commit".
        :type message: string
        :param author:
            (optional) The signature for the author of the first commit.
            Defaults to global author.
        :type author: pygit2.Signature
        :param committer:
            (optional) The signature for the committer of the first commit.
            Defaults to author.
        :type author: pygit2.Signature

        :returns: the jsongit
        :rtype: :class:`jsongit <jsongit>`
        """
        self.raw_commit(key, data, author, committer, message, [])
        return self.get(key, autocommit=autocommit)

    def has(self, key):
        """Determine whether there is an entry for key in this repository.

        :param key: The key to check
        :type key: string

        :returns: whether there is an entry
        :rtype: boolean
        """
        try:
            self._repo.lookup_reference(self._key_to_ref(key))
            return True
        except KeyError:
            return False

    def get(self, key, autocommit=False):
        """Obtain the :class:`jsongit <jsongit>` for a key.

        :param key: The key to look up.
        :type key: string
        :param autocommit:
            (optional) Whether the :class:`jsongit <jsongit>` should
            automatically commit. Defaults to false.
        :type autocommit: boolean

        :returns: the jsongit
        :rtype: :class:`jsongit <jsongit>`
        :raises: KeyError if there is no entry for key
        """
        return JsonGitObject(self, key, autocommit=autocommit)

    def fast_forward(self, from_key, to_key):
        """Fast forward a :class:`jsongit <jsongit>`.

        :param from_key: the key of the entry to fast forward
        :type from_key: string
        :param to_key: the key of the entry to fast forward to
        :type to_key: string
        """
        from_ref = self._key_to_ref(from_key)
        self._repo.lookup_reference(from_ref).delete()
        self._repo.create_reference(from_ref, self.get_commit_oid_for_key(to_key))

    def clone(self, source, dest, autocommit=False):
        """Clone a :class:`jsongit <jsongit>`.

        :param source: The key of the source
        :type source: string
        :param dest: The key of the destination
        :type dest: string
        :param autocommit: whether the new object should have autocommit enabled
        :type autocommit: bool

        :return: A new :class:`JsonGitObject <JsonGitObject>`
        :rtype: :class:`JsonGitObject <JsonGitObject>`
        :raises: ValueError if to_key already exists.
        """
        try:
            self._repo.create_reference(self._key_to_ref(dest),
                                        self.get_commit_oid_for_key(source))
            return self.get(dest, autocommit=autocommit)
        except GitError:
            raise ValueError('Cannot clone to %s, there is already a dict there.' % dest)


# -*- coding: utf-8 -*-

"""
gitdict.repository
"""

import os
from .dict import GitDict
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
    :param author:
        (optional) An optional author to use by default.  This makes it
        possible to commit without having to specify a signature.
    :type author: :class:`DictAuthor <DictAuthor>`
    """

    def __init__(self, path, author=None):

        #: A :class:`DictAuthor <DictAuthor>` used by default when
        #: committing in this repo.
        self.author = author

        if os.path.isdir(path):
            self._repo = Repository(path)
        else:
            self._repo = init_repository(path, True) # bare repo

    def _key_to_ref(self, key):
        return 'refs/%s/HEAD' % key

    def get_commit_oid_for_key(self, key):
        return self._repo[self._repo.lookup_reference(self._key_to_ref(key)).oid].oid

    def get_raw_dict_for_commit_oid(self, commit_oid):
        return json.loads(self._repo[self._repo[commit_oid].tree[DATA].oid].data)

    def get_parent_oids_for_commit_oid(self, commit_oid):
        return [parent.oid for parent in self._repo[commit_oid].parents]

    def raw_commit(self, key, raw_dict, author, committer, message, parents):
        """Commit a dict to this :class:`DictRepository <DictRepository>`.
        It is recommended that you use the :class:`GitDict <GitDict>` commit
        method instead.

        :param raw_dict: the data to commit.
        :type raw_dict: dict
        :param author: The author of the commit.
        :type author: pygit2.Signature
        :param committer: The committer of this commit.
        :type committer: pygit2.Signature
        :param message: The commit message.
        :type message: string
        :param parents:
            A list of 20-byte object IDs of parent commits.  An empty list
            means this is the first commit.

        :return: The oid of the new commit.
        :rtype: 20 bytes
        """
        if not isinstance(raw_dict, dict):
            raise ValueError("%s is not a dict" % raw_dict)

        blob_id = self._repo.write(GIT_OBJ_BLOB, json.dumps(raw_dict))

        # TreeBuilder doesn't support inserting into trees, so we roll our own
        tree_id = self._repo.write(GIT_OBJ_TREE, '100644 %s\x00%s' % (DATA, blob_id))

        return self._repo.create_commit(self._key_to_ref(key), author,
                                        committer, message, tree_id, parents)

    def create(self, key, dict={}, autocommit=False, author=None):
        """Create a new :class:`DictGit <DictGit>`

        :param key: The key of the new :class:`GitDict <GitDict>`
        :type key: :class:`GitDict <GitDict>`
        :param dict: (optional) The value of the dict.  Defaults to empty.
        :type dict: dict
        :param autocommit:
            (optional) Whether the :class:`GitDict <GitDict>` should
            automatically commit. Defaults to false.
        :type autocommit: boolean
        :param author:
            (optional) A default author for the :class:`GitDict <GitDict>`.
            Defaults to the default author for the repository.
        :type author: :class:`DictAuthor <DictAuthor>`

        :returns: the GitDict
        :rtype: :class:`GitDict <GitDict>`
        """
        author = author or self.author
        self.raw_commit(key, dict, author.signature(), author.signature(),
                           'first commit', [])
        return self.get(key, autocommit=autocommit, author=author)

    def get(self, key, autocommit=False, author=None):
        """Obtain the :class:`GitDict <GitDict>` for a key.

        :param key: The key to look up.
        :type key: string
        :param default:
            (optional) The default dict value if there is no existing value
            for the key.  Defaults to an empty dict.
        :type default: dict
        :param autocommit:
            (optional) Whether the :class:`GitDict <GitDict>` should
            automatically commit. Defaults to false.
        :type autocommit: boolean
        :param author:
            (optional) A default author for the :class:`GitDict <GitDict>`.
            Defaults to the default author for the repository.
        :type author: :class:`DictAuthor <DictAuthor>`

        :returns: the GitDict
        :rtype: :class:`GitDict <GitDict>`
        :raises: KeyError if there is no entry for key
        """
        return GitDict(self, key, autocommit=autocommit, author=author or self.author)

    def fast_forward(self, from_dict, to_dict):
        """Fast forward a :class:`GitDict <GitDict>`.

        :param from_dict: the :class:`GitDict <GitDict>` to fast forward.
        :type from_dict: :class:`GitDict <GitDict>`
        :param to_dict: the :class:`GitDict <GitDict>`to fast forward to.
        :type to_dict: :class:`GitDict <GitDict>`
        """
        from_ref = self.key_to_ref(from_dict.key)
        self._repo.lookup_reference(from_ref).delete()
        self._repo.create_reference(from_ref, self.get_commit_oid_for_key(to_dict.key))

    def clone(self, git_dict, to_key):
        """Clone a :class:`GitDict <GitDict>`.

        :param git_dict: the :class:`GitDict <GitDict>` to clone
        :type git_dict: :class:`GitDict <GitDict>`
        :param to_key: where to clone to
        :type to_key: string
        :raises: ValueError if to_key already exists.
        """
        if self.get_commit_oid_for_key(to_key):
            raise ValueError('Cannot clone to %s, there is already a dict there.' % to_key)
        else:
            self._repo.create_reference(self._key_to_ref(git_dict.key),
                                        self.get_commit_oid_for_key(git_dict.key))

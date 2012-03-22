# -*- coding: utf-8 -*-

"""
jsongit.models

The meat of jsongit code, particularly the Repository, resides here.
"""

import pygit2
import collections
import functools
import shutil
import itertools

from .exceptions import NotJsonError, InvalidKeyError, DifferentRepoError
from .wrappers import Commit, Diff, Conflict, Merge
import constants
import utils

# The name of the only blob within the special commit tree.

class Repository(object):
    def __init__(self, repo, dumps, loads):
        self._repo = repo
        self._global_name = utils.global_config('user.name')
        self._global_email = utils.global_config('user.email')
        self._dumps = dumps
        self._loads = loads

    def __eq__(self, other):
        return self._repo.path == other._repo.path

    def _key2ref(self, key):
        """The keys of a Repository are also references to the head commit
        for that key.  This translates keys to the appropriate path (in
        /refs/heads/jsongit/).

        :raises: InvalidKeyError
        """
        if not isinstance(key, basestring):
            raise InvalidKeyError("%s must be a string to be a key." % key)
        elif key[-1] == '.' or key[-1] == '/':
            raise InvalidKeyError("Key '%s' should not end in . or /" % key)
        else:
            return 'refs/heads/jsongit/%s' % key

    def _insert_repo_entry(self, key, blob_id, author, committer, message):
        """Insert a new piece of data into the repo's tree.
        """
        # TreeBuilder doesn't support inserting into trees, so we roll our own
        head_target = self._repo.lookup_reference('HEAD').target
        try:
            head_commit = self._repo[self._repo.lookup_reference(head_target).oid]
            head_tree = head_commit.tree
            tree_data = b''.join([
                b"%o %s\x00%s" % (e.attributes, e.name, e.oid)  # octal attributes
                for e in head_tree if e.name != key  # skip existing entry
            ])
            parents = [head_commit.oid]
        except KeyError:  # no commit yet for head (first commit to repo),
                          # so we create an empty tree
            tree_data = ''
            parents = []
        tree_data = tree_data + b"100644 %s\x00%s" % (key, blob_id)

        tree_id = self._repo.write(pygit2.GIT_OBJ_TREE, tree_data)
        self._repo.index.read_tree(tree_id)
        self._repo.index.write()
        self._repo.create_commit(head_target, author, committer, message, tree_id, parents)

    def commit(self, key, value, **kwargs):
        """Commit new value to the key.  Maintains relation to parent commits.

        :param key: The key
        :type key: string
        :param value:  The value of the key.
        :type value: anything that runs through :func:`json.dumps`
        :param author:
            (optional) The signature for the author of the first commit.
            Defaults to global author.
        :param message:
            (optional) Message for first commit.  Defaults to "adding [key]" if
            there was no prior value.
        :type message: string
        :param author:
            (optional) The signature for the committer of the first commit.
            Defaults to global author.
        :type author: pygit2.Signature
        :param committer:
            (optional) The signature for the committer of the first commit.
            Defaults to author.
        :type committer: pygit2.Signature
        :param parents:
            (optional) The parents of this commit.  Defaults to the last commit
            for this key if it already exists, or an empty list if not.
        :type parents: list of :class:`Commit`

        :raises: NotJsonError, InvalidKeyError
        """
        message = kwargs.pop('message', '' if self.has(key) else 'adding %s' % key)
        parents = kwargs.pop('parents', [self.get(key)] if self.has(key) else [])
        author = kwargs.pop('author', utils.signature(self._global_name,
                                                      self._global_email))
        committer = kwargs.pop('committer', author)
        if kwargs:
            raise TypeError("Unknown keyword args %s" % kwargs)

        try:
            blob_id = self._repo.write(pygit2.GIT_OBJ_BLOB, self._dumps(value))
        except ValueError as e:
            raise NotJsonError(e)
        except TypeError as e:
            raise NotJsonError(e)

        self._insert_repo_entry(key, blob_id, author, committer, message)

        tree_id = self._repo.write(pygit2.GIT_OBJ_TREE, b"100644 %s\x00%s" % (key, blob_id))
        try:
            self._repo.create_commit(self._key2ref(key), author,
                                     committer, message, tree_id,
                                     [parent.oid for parent in parents])
        except pygit2.GitError as e:
            if str(e).startswith('Failed to create reference'):
                raise InvalidKeyError(e)
            else:
                raise e

    def destroy(self):
        """Erase this Git repository entirely.  This will remove its directory.
        Methods called on a repository or its objects after it is destroyed
        will throw exceptions.
        """
        shutil.rmtree(self._repo.path)
        self._repo = None

    def has(self, key):
        """Determine whether there is an entry for key in this repository.

        :param key: The key to check
        :type key: string

        :returns: whether there is an entry
        :rtype: boolean
        """
        try:
            return key in self._repo.index
        except TypeError as e:
            raise InvalidKeyError(e)
        # try:
        #     self._repo.lookup_reference(self._key2ref(key))
        #     return True
        # except KeyError:
        #     return False

    def fork(self, dest, key=None, commit=None, **kwargs):
        """Create a new key at dest if it does not exist whose first commit
        will point to the head of the specified key or commit.

        :param key:
            (optional) the key of the fork source, which will use the head
            commit.
        :type key: string
        :param commit: (optional) the explicit commit to fork
        :type commit: :class:`Commit`
        :param author:
            (optional) The author of the commit.  Defaults to global author.
        :type author: pygit2.Signature
        :param committer:
            (optional) The committer of the commit.  Will default to global author.
        :type committer: pygit2.Signature

        :raises: KeyError if there is already a key at dest.
        """
        if self.has(dest):
            raise KeyError("Cannot fork to %s, there is already a key there." % dest)
        if commit is None:
            commit = self.get(key)
        if commit.key == dest:
            raise ValueError('I can see you\'ve played knifey-spooney (a key can\'t fork itself)')
        else:
            message = "Forking %s from %s" % (dest, commit.key)
            self.commit(dest, commit.value, message=message, parents=[commit])

    def get(self, key, back=0):
        """Obtain a :class:`Commit` associated with a key.

        :param key: The key to look up.
        :type key: string
        :param back:
            (optional) How many steps back from head to get the commit.
            Defaults to 0 (the most recent).
        :type back: integer

        :returns: the wrapped data
        :rtype: :class:`Commit`
        :raises:
            KeyError if there is no entry for key, IndexError if too many steps
            back are specified.
        """
        try:
            return itertools.islice(self.log(key), back, back + 1).next()
        except KeyError:
            raise KeyError("There is no key at %s" % key)
        except StopIteration:
            raise IndexError("%s has fewer than %s commits" % (key, back))

    def merge(self, dest, key=None, commit=None, **kwargs):
        """Try to merge two commits together.

        :param dest: the key to receive the merge
        :type dest: string
        :param key:
            (optional) the key of the merge source, which will use the head
            commit.
        :type key: string
        :param commit: (optional) the explicit commit to merge
        :type commit: :class:`Commit`
        :param author:
            (optional) The author of this commit, if one is necessary.
            Defaults to global author.
        :type author: pygit2.Signature
        :param committer:
            (optional) The committer of this commit, if one is necessary.
            Will default to global author.
        :type committer: pygit2.Signature

        :returns: The results of the merge operation
        :rtype: :class:`Merge`
        """
        if commit is None:
            commit = self.get(key)
        if commit.key == dest:
            raise ValueError('Cannot merge a key with itself')

        dest_head = self.get(dest)
        # No difference
        if commit.oid == dest_head.oid:
            return Merge(True, commit, dest_head, "Same commit", result=commit)

        # Do a merge if there were no overlapping changes
        # First, find the shared parent
        try:
            shared_commit = (dc for dc in self.log(commit=dest_head)
                             if dc.oid in (sc.oid for sc in self.log(commit=commit))).next()
        except StopIteration:
            return Merge(False, commit, dest_head, "No shared parent")

        # Now, see if the diffs conflict
        source_diff = Diff(shared_commit.value, commit.value)
        dest_diff = Diff(shared_commit.value, dest_head.value)

        conflict = Conflict(source_diff, dest_diff)

        # No-go, the user's gonna have to figure this one out
        if conflict:
            return Merge(False, commit, dest_head, "Merge conflict",
                                conflict=conflict)
        # Sweet. we can apply all the diffs.
        else:
            merged_data = dest_diff.apply(source_diff.apply(shared_commit.value))
            message = "Auto-merge of %s and %s from shared parent %s" % (
                commit.hex[0:10], dest_head.hex[0:10], shared_commit.hex[0:10])
            parents = [dest_head, commit]
            result = self.commit(dest, merged_data, message=message, parents=parents, **kwargs)
            return Merge(True, commit, dest_head, message, result=result)

    def _build_commit(self, pygit2_commit):
        key = pygit2_commit.tree[0].name
        raw = self._repo[self._repo[pygit2_commit.oid].tree[key].oid].data
        value = self._loads(raw)
        return Commit(self, key, value, pygit2_commit)
#         raw_data = self._repo[self._repo[c.oid].tree[commit.key].oid].data
#             return Commit(self, commit, self._loads(raw_data))

    def log(self, key=None, commit=None, order=constants.GIT_SORT_TOPOLOGICAL):
        """ Traverse commits from the specified key or commit.  Must specify
        one or the other.

        :param key:
            (optional) The key to look up a log for.  Will look from the head
            commit.
        :type key: string
        :param commit:
            (optional) An explicit commit to look up log for.
        :type commit: :class:`Commit`
        :param order:
            (optional) Flags to order traversal.  Valid flags are in
            :mod:`constants`.  Defaults to :const:`GIT_SORT_TOPOLOGICAL`
        :type order: number

        :returns:
            A generator to traverse commits, yielding :class:`Commit` objects.
        :rtype: generator
        """
        if commit is None:
            c = self._repo[self._repo.lookup_reference(self._key2ref(key)).oid]
            commit = self._build_commit(c)
        return (self._build_commit(c) for c in self._repo.walk(commit.oid, order))

    def remove(self, key):
        """Remove the head reference to this key, so that it is no longer
        visible in the repo.  Prior commits and blobs remain in the repo.
        """
        raise NotImplementedError()


# class Object(collections.MutableMapping, collections.MutableSequence):
# 
#     def dirtify(meth):
#         """Decorator that dirties up the object upon successful completion.
#         """
#         @functools.wraps(meth)
#         def wrapped(self, *args, **kwargs):
#             retval = meth(self, *args, **kwargs)
#             self._dirty = True  # if above call fails, we're not dirtied.
#             if self.autocommit:
#                 self.commit()
#             return retval
#         return wrapped
# 
#     def __init__(self, repo, commit, value, autocommit):
# 
#         #: Whether changes should be automatically committed.
#         self.autocommit = autocommit
# 
#         self._repo = repo
#         self._head = commit
#         self._value = value
#         self._dirty = False
# 
#     def _value_meth(self, meth):
#         cls = self.value.__class__
#         try:
#             return getattr(cls, meth)
#         except AttributeError:
#             raise TypeError("%s does not support %s" % (cls, meth))
# 
#     def __contains__(self, item):
#         return self._value_meth('__contains__')(self.value, item)
# 
#     def __len__(self):
#         return self._value_meth('__len__')(self.value)
# 
#     def __iter__(self):
#         return self._value_meth('__iter__')(self.value)
# 
#     def __getitem__(self, key):
#         return self._value_meth('__getitem__')(self.value, key)
# 
#     @dirtify
#     def __setitem__(self, key, value):
#         return self._value_meth('__setitem__')(self.value, key, value)
# 
#     @dirtify
#     def __delitem__(self, key):
#         return self._value_meth('__delitem__')(self.value, key)
# 
#     @dirtify
#     def insert(self, item):
#         return self._value_meth('insert')(self.value, item)
# 
#     def __str__(self):
#         return self._value
# 
#     def __repr__(self):
#         return '%s(key=%s,value=%s,dirty=%s)' % (
#             type(self).__name__,
#             self.key,
#             self._value.__repr__(),
#             self.dirty)
# 
#     def _update(self, commit=None):
#         if commit is None:
#             commit = self._repo.get(self.key).head
#         self._value = commit.object.value
#         self._head = commit
#         self._dirty = False
# 
#     @property
#     def repo(self):
#         """The :class:`Repository` of this object.
#         """
#         return self._repo
# 
#     @property
#     def key(self):
#         """The String key for this dict in its repository.
#         """
#         return self.head.key
# 
#     @property
#     def dirty(self):
#         """Whether the current value is different than what's in the repo.
#         """
#         return self._dirty
# 
#     @property
#     def value(self):
#         """The current (possibly dirty) value of this object.
#         """
#         return self._value
# 
#     @property
#     def head(self):
#         """The :class:`Commit` last associated with this object.
#         """
#         return self._head
# 
#     def commit(self, **kwargs):
#         """Convenience wrapper for :func:`Repository.commit` applying to this
#         key.  Resets the dirty flag and updates head.
#         """
#         commit = self.repo.commit(self.key, self.value, **kwargs).head
#         self._update(commit=commit)
#         assert self.value == commit.object.value
# 
#     def log(self, **kwargs):
#         """Convenience wrapper for :func:`Repository.log` applying to this key.
#         Returns the log based off this object's head, which may not be the
#         most recent commit for the key in the repository.
#         """
#         return self.repo.log(commit=self.head, **kwargs)
# 
#     def merge(self, other, **kwargs):
#         """Convenience wrapper for :func:`Repository.commit`
# 
#         :param other:
#             the object to merge in.  The merge is done to the head of
#             this object.
#         :type other: :class:`Object`
# 
#         :raises: DifferentRepoError
#         """
#         if other.repo == self.repo:
#             merge = self.repo.merge(self.key, commit=other.head, **kwargs)
#             if merge.success:
#                 self._update()
#             return merge
#         else:
#             # this would run, but would break references in future.
#             raise DifferentRepoError("Cannot merge object in, it's in a \
#                                      different repo")
# 
#     def fork(self, dest_key, **kwargs):
#         """Convenience wrapper for :func:`Repository.fork`
# 
#         :param dest_key:
#             the key to fork to.
#         :type dest_key: string
#         """
#         return self.repo.fork(dest_key, commit=self.head)
# 

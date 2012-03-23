# -*- coding: utf-8 -*-

"""
jsongit.models

The meat of jsongit code, particularly the Repository, resides here.
"""

import pygit2
# import collections
# import functools
import shutil
import itertools

from .exceptions import (
    NotJsonError, InvalidKeyError, DifferentRepoError, StagedDataError)
from .wrappers import Commit, Diff, Conflict, Merge
import constants
import utils

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
        elif key[-1] == '.' or key[-1] == '/' or key[0] == '/' or key[0] == '.':
            raise InvalidKeyError("Key '%s' should not start or end in . or /" % key)
        else:
            return 'refs/heads/jsongit/%s' % key

    def _build_commit(self, key, pygit2_commit):
        assert key in pygit2_commit.tree
        raw = self._repo[pygit2_commit.tree[key].oid].data
        value = self._loads(raw)
        return Commit(self, key, value, pygit2_commit)

    def _head_target(self):
        return self._repo.lookup_reference('HEAD').target

    def _repo_head(self):
        try:
            return self._repo[self._repo.lookup_reference(self._head_target()).oid]
        except KeyError:
            return None

    def add(self, key, value):
        """Add a value for a key to the working tree, staging it for commit.

        :param key: The key to add
        :type key: string
        :param value: The value to insert
        :param value:  The value of the key.

        :type value: anything that runs through :func:`json.dumps`
        :raises: NotJsonError, InvalidKeyError
        """
        self._key2ref(key) # throw InvalidKeyError
        try:
            blob_id = self._repo.write(pygit2.GIT_OBJ_BLOB, self._dumps(value))
        except ValueError as e:
            raise NotJsonError(e)
        except TypeError as e:
            raise NotJsonError(e)

        if key in self._repo.index:
            del self._repo.index[key]
        working_tree_id = self._repo.index.write_tree()
        working_tree = self._repo[working_tree_id]
        new_entry = b"100644 %s\x00%s" % (key, blob_id)
        tree_data = working_tree.read_raw() + new_entry
        working_tree_id = self._repo.write(pygit2.GIT_OBJ_TREE, tree_data)
        self._repo.index.read_tree(working_tree_id)
        self._repo.index.write()

        # replace existing working entry
        # if key in working_tree:
        #     tree_data = b''.join([
        #         new_entry
        #         if e.name == key
        #         else b"%o %s\x00%s" % (e.attributes, e.name, e.oid)  # octal attributes
        #         for e in working_tree
        #     ])
        # # add the new entry
        # else:

    def checkout(self, source, dest, **kwargs):
        """ Replace the HEAD reference for dest with a commit that points back
        to the value at source.

        :param source: The source key.
        :type source: string
        :param dest: The destination key
        :type dest: string
        :param author:
            (optional) The author of the commit.  Defaults to global author.
        :type author: pygit2.Signature
        :param committer:
            (optional) The committer of the commit.  Will default to global author.
        :type committer: pygit2.Signature

        :raises: StagedDataError
        """
        message = "Checkout %s from %s" % (dest, source)
        commit = self.head(source)
        self.commit(dest, commit.data, message=message, parents=[commit])

    def commit(self, key=None, value=None, add=True, **kwargs):
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
        keys = [key] if key is not None else [e.path for e in self._repo.index]
        message = kwargs.pop('message', '')
        parents = kwargs.pop('parents', None)
        author = kwargs.pop('author', utils.signature(self._global_name,
                                                      self._global_email))
        committer = kwargs.pop('committer', author)
        if kwargs:
            raise TypeError("Unknown keyword args %s" % kwargs)
        if key is None and value is not None:
            raise InvalidKeyError()

        if parents is not None:
            for parent in parents:
                if parent.repo != self:
                    raise DifferentRepoError()

        if add is True and key is not None and value is not None:
            self.add(key, value)

        repo_head = self._repo_head()
        tree_id = self._repo.index.write_tree()
        self._repo.create_commit(self._head_target(), author, committer,
                                 message, self._repo.index.write_tree(),
                                [repo_head.oid] if repo_head else [])

        #tree_id = self._repo.write(pygit2.GIT_OBJ_TREE, b"100644 %s\x00%s" % (key, blob_id))
        # TODO This will create some keys but not others if there is a bad key
        for key in keys:
            if parents is None:
                parents = [self.head(key)] if self.committed(key) else []
            try:
                self._repo.create_commit(self._key2ref(key), author,
                                         committer, message, tree_id,
                                         [parent.oid for parent in parents])
            except pygit2.GitError as e:
                if str(e).startswith('Failed to create reference'):
                    raise InvalidKeyError(e)
                else:
                    raise e

    def committed(self, key):
        """Determine whether there is a commit for a key.

        :param key: the key to check
        :type key: string

        :returns: whether there is a commit for the key.
        :rtype: boolean
        """
        try:
            self._repo.lookup_reference(self._key2ref(key))
            return True
        except KeyError:
            return False

    def destroy(self):
        """Erase this Git repository entirely.  This will remove its directory.
        Methods called on a repository or its objects after it is destroyed
        will throw exceptions.
        """
        shutil.rmtree(self._repo.path)
        self._repo = None

    def head(self, key, back=0):
        """Get the head commit for a key.

        :param key: The key to look up.
        :type key: string
        :param back:
            (optional) How many steps back from head to get the commit.
            Defaults to 0 (the current head).
        :type back: integer

        :returns: the data
        :rtype: int, float, NoneType, unicode, boolean, list, or dict
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

    def index(self, key):
        """Pull the current data for key from the index.

        :param key: the key to get data for
        :type key: string

        :returns: a value
        :rtype: None, unicode, float, int, dict, list, or boolean
        """
        self._repo.index.read()
        raw = self._repo[self._repo.index[key].oid].data
        return self._loads(raw)

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
            commit = self.head(key)
        if commit.key == dest:
            raise ValueError('Cannot merge a key with itself')

        dest_head = self.head(dest)
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
        if key is None and commit is None:
            raise TypeError()
        elif commit is None:
            c = self._repo[self._repo.lookup_reference(self._key2ref(key)).oid]
            commit = self._build_commit(key, c)
        return (self._build_commit(commit.key, c)
                for c in self._repo.walk(commit.oid, order) if commit.key in c.tree)

    def remove(self, key, force=False):
        """Remove the head reference to this key, so that it is no longer
        visible in the repo.  Prior commits and blobs remain in the repo, but
        inaccessible through this interface.

        :param key: The key to remove
        :type key: string
        :param force:
            (optional) Whether to remove the HEAD reference even if
            there is data staged in the index but not yet committed.  If force
            is true, the index entry will be removed as well.
        :type force: boolean

        :raises: StagedDataError
        """
        if force is True or self.staged(key) is False:
            del self._repo.index[key]
        elif force is False and self.staged(key):
            raise StagedDataError("There is data staged for %s" % key)
        self._repo.lookup_reference(self._key2ref(key)).delete()

    def reset(self, key):
        """Reset the value in the index to its HEAD value.

        :param key: the key to reset
        :type key: string
        """
        self.add(key, self.head(key).data)

    def show(self, key, back=0):
        """Obtain the data at HEAD, or a certain number of steps back, for key.

        :param key: The key to look up.
        :type key: string
        :param back:
            (optional) How many steps back from head to get the commit.
            Defaults to 0 (the current head).
        :type back: integer

        :returns: the data
        :rtype: int, float, NoneType, unicode, boolean, list, or dict
        :raises:
            KeyError if there is no entry for key, IndexError if too many steps
            back are specified.
        """
        return self.head(key, back=back).data

    def staged(self, key):
        """Determine whether the value in the index differs from the committed
        value.

        :param key: The key to check
        :type key: string

        :returns: whether the entries are different.
        :rtype: boolean
        """
        if key in self._repo.index:
            if self.committed(key):
                return self.index(key) != self.show(key)
            else:
                return True
        else:
            return False
        # try:
        #     self._repo.lookup_reference(self._key2ref(key))
        #     return True
        # except KeyError:
        #     return False

# class Value(object):
#     """Values are what exist behind a single key.  They provide convenience
#     methods to their underlying repository.
#     """
# 
#     def __init__(self, repo, key, data):
#         self._repo = repo
#         self._key = key
#         self._data = data
# 
#     def add(self, **kwargs):
#         """Convenience method to add this value to the repository.
#         """
#         self.repo.add(self._key, self._data, **kwargs)
# 
#     def commit(self, **kwargs):
#         """Convenience method to commit this value to the repository.  By
#         default will `add` as well.
#         """
#         self.repo.commit(self._key, self._data, **kwargs)
# 
#     @property
#     def committed(self):
#         """Whether this key has been committed to the repository.
#         """
#         return self.repo.head(self._key)[self._key].data == self.data
# 
#     @property
#     def data(self):
#         """Returns the data for this key.
#         """
#         return self._data
# 
#     def head(self, **kwargs):
#         """Convenience method to get the head commit for this value's key from
#         the repository.
#         """
#         return self.repo.head(self._key, **kwargs)
# 
#     def log(self, **kwargs):
#         """Convenience method to get the log for this value's key.
#         """
#         return self.repo.log(self._key, **kwargs)
# 
#     @property
#     def repo(self):
#         """The repository.
#         """
#         return self._repo
# 
#     @property
#     def staged(self):
#         """Whether the data in this key has been staged to be committed to the
#         repository (added, but not committed.)
#         """
#         return self.repo.staged(self._key)
# 
#     def unstage(self):
#         """Unstage this key if it has been added, but not committed.
#         """
#         self.repo.unstage(self._key)
# 
#     def remove(self):
#         """Convenience method to remove this key from the repository.
#         """
#         self.remove(self._key)




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

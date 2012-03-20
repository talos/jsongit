# -*- coding: utf-8 -*-

"""
jsongit.models

The meat of jsongit code, particularly the Repository, resides here.
"""

import pygit2
import collections
import functools
import shutil

from .exceptions import NotJsonError, BadKeyTypeError, DifferentRepoError
from .wrappers import Commit, Diff, Conflict, Merge
import constants
import utils

# The name of the only blob within the tree.
DATA = 'data'


class Repository(object):
    def __init__(self, repo, dumps, loads):
        self._repo = repo
        self._global_name = utils.global_config('user.name')
        self._global_email = utils.global_config('user.email')
        self._dumps = dumps
        self._loads = loads

    def __eq__(self, other):
        return self._repo.path == other._repo.path

    def _translate_key(self, key):
        """The keys of a Repository are actually references to a head commit.
        This translates keys to the appropriate path (in /refs/heads/).
        """
        if isinstance(key, basestring):
            return 'refs/heads/%s' % key
        else:
            raise BadKeyTypeError("%s must be a string to be a string." % key)

    def commit(self, key, data, autocommit=False, **kwargs):
        """Commit new data to the key.  Maintains relation to parent commits.

        :param key: The key of the new data.
        :type key: string
        :param data:  The value of the item.
        :type data: anything that runs through :func:`json.dumps`
        :param autocommit:
            whether the retrieved :class:`Object` should autocommit.
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
        :rtype: :class:`Object`

        :raises: NotJsonError, BadKeyTypeError
        """
        message = kwargs.pop('message', '' if self.has(key) else 'first commit')
        parents = kwargs.pop('parents', [self.head(key)] if self.has(key) else [])
        author = kwargs.pop('author', utils.signature(self._global_name,
                                                      self._global_email))
        committer = kwargs.pop('committer', author)
        if kwargs:
            raise TypeError("Unknown keyword args %s" % kwargs)
        try:
            blob_id = self._repo.write(pygit2.GIT_OBJ_BLOB, self._dumps(data))
        except ValueError as e:
            raise NotJsonError(e)
        except TypeError as e:
            raise NotJsonError(e)

        # TreeBuilder doesn't support inserting into trees, so we roll our own
        tree_id = self._repo.write(pygit2.GIT_OBJ_TREE,
                                   '100644 %s\x00%s' % (DATA, blob_id))

        self._repo.create_commit(self._translate_key(key), author,
                                 committer, message, tree_id,
                                 [parent.oid for parent in parents])
        return self.get(key, autocommit=autocommit)

    def destroy(self):
        """Erase this Git repository entirely.  This will remove its directory.
        Methods called on a repository or its objects after it is destroyed
        will throw exceptions.
        """
        shutil.rmtree(self._repo.path)

    def has(self, key):
        """Determine whether there is an entry for key in this repository.

        :param key: The key to check
        :type key: string

        :returns: whether there is an entry
        :rtype: boolean

        :raises: BadKeyTypeError, KeyError
        """
        try:
            self._repo.lookup_reference(self._translate_key(key))
            return True
        except KeyError:
            return False

    def head(self, key, back=0):
        """Obtain a commit for a key relative to head (the most recent).

        :param key: The key to get the commit for
        :type key: string
        :param back:
            (optional) How many steps back from head to get the commit.
            Defaults to 0.
        :type back: integer

        :returns: The head commit
        :rtype: :class:`Commit`

        :raises: BadKeyTypeError, KeyError
        """
        if back == 0:
            ref = self._repo.lookup_reference(self._translate_key(key))
            return Commit(self, self._repo[ref.oid])
        else:
            for i, commit in enumerate(self.log(key)):
                if i == back:
                    return commit
            raise IndexError("More steps back than log")

    def get(self, key=None, commit=None, autocommit=False):
        """Obtain the :class:`Object` associated with a key or commit.  Looking
        up a key is equivalent to looking up its head commit.  You must supply
        a key or a commit.

        :param key: (optional) The key to look up.
        :type key: string
        :param commit: (optional) The commit to look up.
        :type commit: :class:`Commit`
        :param autocommit:
            (optional) Whether the retrieved data should commit when changed.
            Defaults to false.
        :type autocommit: boolean

        :returns: the wrapped data
        :rtype: :class:`Object`
        :raises: KeyError if there is no entry for key
        """
        if commit is None:
            commit = self.head(key)
        raw_data = self._repo[self._repo[commit.oid].tree[DATA].oid].data
        return Object(self, key, commit, self._loads(raw_data), autocommit)

    def fast_forward(self, dest, key=None, commit=None, **kwargs):
        """Fast forward the data at dest.  Loses intervening commits if there
        were any.

        :param dest: the key to be fast forwarded
        :type dest: string
        :param key:
            (optional) the key of the data to fast forward to, defaulting to
            the head commit.
        :type key: string
        :param commit: (optional) the commit to fast forward to.
        :type commit: :class:`Commit`

        :returns: the wrapped data at dest
        :rtype: :class:`Object`
        :raises: KeyError, BadKeyTypeError
        """
        if commit is None:
            commit = self.head(key)
        if key == dest:
            raise ValueError('Cannot fast forward key to itself')
        dest_ref = self._translate_key(dest)
        # TODO: require a force flag in this case?
        if self.has(dest):
            self._repo.lookup_reference(dest_ref).delete()
        self._repo.create_reference(dest_ref, commit.oid)

        return self.get(dest, **kwargs)

    def merge(self, dest, key=None, commit=None, **kwargs):
        """Try to merge two keys together.  If possible, will fast-forward,
        otherwise, will try to merge in the intervening changes.

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
        :rtype: :class:`JsonMerge`
        """
        if commit is None:
            commit = self.head(key)
        dest_head = self.head(dest)
        # No difference
        if commit.oid == dest_head.oid:
            return Merge(True, commit, dest_head, "Same commit")

        # Test if a fast-forward is possible
        if any(dest_head.oid in c.oid for c in self.log(commit=commit)):
            self.fast_forward(dest, commit=commit)
            return Merge(True, commit, dest_head, "Fast forward")

        # Do a merge if there were no overlapping changes
        # First, find the shared parent
        try:
            shared_commit = (dc for dc in self.log(commit=dest_head)
                             if dc.oid in (sc.oid for sc in self.log(commit=commit))).next()
        except StopIteration:
            return Merge(False, commit, dest_head, "No shared parent")

        # Now, see if the diffs conflict
        source_diff = Diff(shared_commit.object.value, commit.object.value)
        dest_diff = Diff(shared_commit.object.value, dest_head.object.value)

        conflict = Conflict(source_diff, dest_diff)

        # No-go, the user's gonna have to figure this one out
        if conflict:
            return Merge(False, commit, dest_head, "Merge conflict",
                                conflict=conflict)
        # Sweet. we can apply all the diffs.
        else:
            merged_data = dest_diff.apply(source_diff.apply(shared_commit.object.value))
            message = "Auto-merge from %s" % shared_commit.hex
            parents = [commit, dest_head]
            self.commit(dest, merged_data, message=message, parents=parents, **kwargs)
            return Merge(True, commit, dest_head, message)

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
            commit = self.head(key)
        return (Commit(self, c) for c in self._repo.walk(commit.oid, order))


class Object(collections.MutableMapping, collections.MutableSequence):

    def dirtify(meth):
        """Decorator that dirties up the object upon successful completion.
        """
        @functools.wraps(meth)
        def wrapped(self, *args, **kwargs):
            retval = meth(self, *args, **kwargs)
            self._dirty = True  # if above call fails, we're not dirtied.
            if self.autocommit:
                self.commit()
            return retval
        return wrapped

    def __init__(self, repo, key, head, value, autocommit):

        #: Whether changes should be automatically committed.
        self.autocommit = autocommit

        self._repo = repo
        self._key = key
        self._head = head
        self._value = value
        self._dirty = False

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

    @dirtify
    def __setitem__(self, key, value):
        return self._value_meth('__setitem__')(self.value, key, value)

    @dirtify
    def __delitem__(self, key):
        return self._value_meth('__delitem__')(self.value, key)

    @dirtify
    def insert(self, item):
        return self._value_meth('insert')(self.value, item)

    def __repr__(self):
        return '%s(key=%s,value=%s,dirty=%s)' % (
            type(self).__name__,
            self.key,
            self._value.__repr__(),
            self.dirty)

    def _read(self):
        updated = self._repo.get(self.key)
        self._value = updated.value
        self._head = updated.head
        self._dirty = False

    @property
    def repo(self):
        """The :class:`Repository` of this object.
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

    @property
    def head(self):
        """The head :class:`Commit` for this object.
        """
        return self._head

    def commit(self, **kwargs):
        """Convenience wrapper for :func:`Repository.commit` applying to this
        key.  Resets the dirty flag and updates head.
        """
        updated = self.repo.commit(self.key, self.value, **kwargs)
        assert self._value == updated.value
        self._head = updated.head
        self._dirty = False

    def log(self, **kwargs):
        """Convenience wrapper for :func:`Repository.log` applying to this key.
        Returns the log based off this object's head, which may not be the
        most recent commit for the key in the repository.
        """
        return self.repo.log(commit=self.head, **kwargs)

    def merge(self, other, **kwargs):
        """Convenience wrapper for :func:`Repository.commit`

        :param other:
            the object to merge in.  The merge is done to the head of
            this object.
        :type other: :class:`Object`

        :raises: DifferentRepoError
        """
        if not isinstance(other, Object):
            raise ValueError('Can only merge in another Object')
        if other.repo == self.repo:
            merge = self.repo.merge(self.key, commit=other.head, **kwargs)
            if merge.success:
                self._read()
            return merge
        else:
            raise DifferentRepoError("Cannot merge object in, it's in a \
                                     different repo")

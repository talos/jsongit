# -*- coding: utf-8 -*-

"""
jsongit.models
"""

import pygit2
import json_diff
import collections
import functools

from .exceptions import NotJsonError, BadKeyTypeError, DifferentRepoError
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

    def _key_to_ref(self, key):
        if isinstance(key, basestring):
            return 'refs/%s/HEAD' % key
        else:
            raise BadKeyTypeError("%s must be a string to be a string." % key)

    def _head_for_key(self, key):
        return self._repo[self._repo.lookup_reference(self._key_to_ref(key)).oid]

    def _data_for_commit(self, commit):
        return self._loads(self._repo[self._repo[commit.oid].tree[DATA].oid].data)

    def _all_commits(self, key):
        head = self._head_for_key(key)
        ancestors = []
        while head:
            ancestors.append(head)
            parents = head.parents
            if len(parents) == 1: # TODO use repo.walk?
                head = parents[0]
            else:
                break
        return ancestors

    def _raw_commit(self, key, data, message, parents, **kwargs):
        """
        :raises: NotJsonError, BadKeyTypeError
        """
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

        self._repo.create_commit(self._key_to_ref(key), author,
                                 committer, message, tree_id, parents)

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
        parents = kwargs.pop('parents', [self._head_for_key(key).oid] if self.has(key) else [])
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
        :rtype: :class:`Object`
        :raises: KeyError if there is no entry for key
        """
        if 'default' in kwargs:
            try:
                return object.Object(self, key, autocommit=autocommit)
            except KeyError:
                return kwargs['default']
        else:
            return object.Object(self, key, autocommit=autocommit)

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
        :rtype: :class:`Object`
        :raises: KeyError, BadKeyTypeError
        """
        if source == dest:
            raise ValueError()
        dest_ref = self._key_to_ref(dest)
        if self.has(dest):
            self._repo.lookup_reference(dest_ref).delete()
        self._repo.create_reference(dest_ref, self._head_for_key(source).oid)

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

        :returns: The results of the merge operation
        :rtype: :class:`JsonMerge`
        """
        source_head, dest_head = [self._head_for_key(k) for k in [source, dest]]
        # No difference
        if source_head.oid == dest_head.oid:
            return Merge(True, source_head, dest_head, "Same commit")

        # Test if a fast-forward is possible
        source_commit_oids = [c.oid for c in self._all_commits(source)]
        if dest_head.oid in source_commit_oids:
            self.fast_forward(source, dest)
            return Merge(True, source_head, dest_head, "Fast forward")

        # Do a merge if there were no overlapping changes
        # First, find the shared parent
        dest_commit_oids = [c.oid for c in self._all_commits(dest)]
        try:
            shared_commit_oid = (oid for oid in dest_commit_oids
                                 if oid in source_commit_oids).next()
        except StopIteration:
            return Merge(False, source_head, dest_head, "No shared parent")

        # Now, see if the diffs conflict
        shared_commit = self._repo[shared_commit_oid]
        shared_data = self._data_for_commit(shared_commit)
        source_data = self._data_for_commit(dest_head)
        dest_data = self._data_for_commit(dest_head)

        source_diff = Diff(shared_data, source_data)
        dest_diff = Diff(shared_data, dest_data)

        conflict = source_diff.conflict(dest_diff)

        # No-go, the user's gonna have to figure this one out
        if conflict:
            return Merge(False, source_head, dest_head, "Merge conflict",
                                conflict=conflict)
        # Sweet. we can apply all the diffs.
        else:
            source_diff.apply(shared_data)
            dest_diff.apply(shared_data)
            message = "Auto-merge from %s" % shared_commit.hex
            self._raw_commit(dest, shared_commit_oid, message
                             [source_head.oid, dest_head.oid], **kwargs)
            return Merge(True, source_head, dest_head, message)


class Object(collections.MutableMapping, collections.MutableSequence):

    def dirtify(meth):
        """Decorator that dirties up a JsonGitObject upon successful call.
        """
        @functools.wraps(meth)
        def wrapped(self, *args, **kwargs):
            retval = meth(self, *args, **kwargs)
            self._dirty = True  # if above call fails, we're not dirtied.
            if self.autocommit:
                self.commit()
            return retval
        return wrapped

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
        return '%s(key=%s,value=%s,dirty=%s)' % (type(self).__name__,
                                                         self.key,
                                                         self._value.__repr__(),
                                                         self.dirty)

    def _read(self):
        head_id = self._repo._head_oid_for_key(self.key)
        self._value = self._repo._data_for_commit_oid(head_id)
        self._dirty = False

    @property
    def repo(self):
        """The :class:`JsonGitRepository` of this object.
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

    def commit(self, **kwargs):
        """Convenience wrapper for :func:`JsonGitRepository.commit`
        """
        self.repo.commit(self.key, self.value, **kwargs)
        self._dirty = False

    def merge(self, other, **kwargs):
        """Convenience wrapper for :func:`JsonGitRepository.commit`

        :param other: the object to merge in
        :type other: :class:`JsonGitObject`

        :raises: DifferentRepoError
        """
        if not isinstance(other, Object):
            raise ValueError('Can only merge in another JsonGitObject')
        if other.repo == self.repo:
            if self.repo.merge(other.key, self.key, **kwargs):
                self._read()
                return True
            else:
                return False
        else:
            raise DifferentRepoError("Cannot merge object in, it's in another \
                                     repo")


class DiffWrapper(object):
    def __init__(self, diff):
        if Diff.is_json_diff(diff):
            # wrap recursive updates
            if Diff.UPDATE in diff:
                update = diff[Diff.UPDATE]
                for k, v in update.viewitems():
                    update[k] = DiffWrapper(v)
            self._replace = None
            self._remove = diff.get(Diff.REMOVE, None)
            self._append = diff.get(Diff.APPEND, None)
            self._update = diff.get(Diff.UPDATE, None)
        else:
            self._replace = diff  # diff is none if there are no differences
            self._remove = None
            self._append = None
            self._update = None

        self._diff = diff

    def __str__(self):
        return self._diff.__str__()

    def __repr__(self):
        return self._diff.__repr__()

    def __getitem__(self, k):
        return self._diff[k]
        # if self.replace is not None:
        #     return self.replace[k]
        # else:
        #     raise TypeError("This DiffWrapper is not wrapping a replacement map.")

    def __eq__(self, other):
        return self._diff == other

    @property
    def remove(self):
        """A dict of removed keys and their values.
        """
        return self._remove

    @property
    def update(self):
        """A dict of updated keys and their values.
        """
        return self._update

    @property
    def append(self):
        """A dict of appended keys and their values.
        """
        return self._append

    @property
    def replace(self):
        """The diff is simply to replace wholesale.
        """
        return self._replace

    def apply(self, obj):
        """Modify an object with the changes in this diff.

        :raises: TypeError
        """
        for k, v in self.remove.items():
            obj.pop(k)
        for k, v in self.update.items():
            # Recursive update
            if isinstance(v, Diff):
                v.apply(obj[k])
            else:
                obj[k] = v
        for k, v in self.append.items():
            obj[k] = v

#     def conflicts(self, other):
#         """Determine whether this JSON diff conflicts with another.
# 
#         :param other: another diff
#         :type other: :class:`Diff`
# 
#         :returns: A list of conflicts, of 0-length if there were none
#         :rtype: list
#         """
#         conflicts = []
#         if this.replace != other.replace:
#             conflicts = (this.replace, other.replace)
#         else:
#             for verb_1, verb_2 in itertools.product(['append', 'update', 'remove'],
#                                                     repeat=2):
#                 mod_1 = getattr(diff_1, verb_1)
#                 mod_2 = getattr(diff_2, verb_2)
# 
#                 # If verbs were the same, it's OK unless mod was different.
#                 if verb_1 == verb_2:
#                     if isinstance(mod_1, Diff) and isinstance(mod_2, Diff):
#                         conflict[verb] = (mod_1, mod_2)
# 
#                 # Otherwise, it's a conflict no matter what
#                 else:
#                     conflict[verb]
# 
#         return conflict if len(conflict) else None

      #   for other_mod_key, other_mod_value in other_mods.items():
      #       if other_mod_key in self_mods:
      #           self_mod_value = self_mods[other_mod_key]
      #           # if the mod type is the same, it's OK if the actual
      #           # modification was the same.
      #           if other_mod_type == self_mod_type:
      #               if other_mod_value == self_mods[other_mod_key]:
      #                   pass
      #               else:
      #                   conflicts[other_mod_key] = {
      #                       'other': { other_mod_type: other_mod_value },
      #                       'self' : { self_mod_type: self_mod_value }
      #                   }
      #           # if the mod type was not the same, it's a conflict no
      #           # matter what
      #           else:
      #               conflicts[other_mod_key] = {
      #                   'other': { other_mod_type: other_mod_value },
      #                   'self' : { self_mod_type: self_mod_value }
      #               }



class Diff(DiffWrapper):
    """A class to encapsulate differences between two JSON git objects.

    :param obj1: The original object.
    :type obj1: :class:`JsonGitObject`
    :param obj2: The object to compare to.
    :type obj2: :class:`JsonGitObject`
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
            diff = json_diff.Comparator()._compare_elements(obj1, obj2)
            super(Diff, self).__init__(diff)
        else:
            # if types differ we just replace
            super(Diff, self).__init__(obj2)


class Merge(object):

    def __init__(self, successful, source_commit, dest_commit, message,
                conflict=None):
        self._successful = successful
        self._message = message
        self._source_commit = source_commit
        self._dest_commit = dest_commit
        self._conflict = conflict

    def __nonzero__(self):
        return self._successful

    @property
    def successful(self):
        return self._successful

    @property
    def source_commit(self):
        return self._source_commit

    @property
    def conflict(self):
        return self._conflict


# -*- coding: utf-8 -*-

"""
jsongit.diff
"""

from json_diff import Comparator

class JsonDiff(object):
    """A wrapper around json_diff's dict comparisons.

    :param dict1: The first dict.  Can be a :class:`GitDict <GitDict>`.
    :type dict1: dict
    :param dict2: The second dict.  Can be a :class:`GitDict <GitDict>`.
    :type dict2: dict
    """

    def __init__(self, dict1, dict2):
        self._diff = Comparator().compare_dicts(dict1, dict2)
        # todo inspect the diff for interior comparison dicts

    @property
    def removed(self):
        """A dict of removed keys and their values.
        """
        return self._diff.get('_remove', {})

    @property
    def updated(self):
        """A dict of updated keys and their values.
        """
        return self._diff.get('_update', {})

    @property
    def appended(self):
        """A dict of appended keys and their values.
        """
        return self._diff.get('_append', {})

    def conflict(self, other):
        """Determine whether this :class:`DictDiff <DictDiff>`s conflicts with
        another.

        :param other: The diff to compare.
        :type other: :class:`DictDiff <DictDiff>`

        :return: the conflicts
        :rtype: :class:`DictConflict <DictConflict>`
        """
        conflicts = {}
        for other_mod_type, other_mods in other._diff.items():
            for self_mod_type, self_mods in self._diff.items():
                for other_mod_key, other_mod_value in other_mods.items():
                    if other_mod_key in self_mods:
                        self_mod_value = self_mods[other_mod_key]
                        # if the mod type is the same, it's OK if the actual
                        # modification was the same.
                        if other_mod_type == self_mod_type:
                            if other_mod_value == self_mods[other_mod_key]:
                                pass
                            else:
                                conflicts[other_mod_key] = {
                                    'other': { other_mod_type: other_mod_value },
                                    'self' : { self_mod_type: self_mod_value }
                                }
                        # if the mod type was not the same, it's a conflict no
                        # matter what
                        else:
                            conflicts[other_mod_key] = {
                                'other': { other_mod_type: other_mod_value },
                                'self' : { self_mod_type: self_mod_value }
                            }
        return conflicts if len(conflicts) else None

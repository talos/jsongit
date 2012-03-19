# -*- coding: utf-8 -*-

from jsongit.models import Diff, Conflict
import helpers
import itertools


class DiffTest(helpers.unittest.TestCase):

    @property
    def fixtures(self):
        return [ 'foo', 7,
                ['foo', 'bar', 'baz'],
                {'roses': 'red', 'violets':'blue'}]

    def test_diff_different_types_favor_second(self):
        for a, b in itertools.permutations(self.fixtures, 2):
            diff = Diff(a, b)
            self.assertEquals(b, diff.replace)
            self.assertEquals(b, diff.apply(a))

    def test_no_changes(self):
        for f in self.fixtures:
            diff = Diff(f, f)
            self.assertIsNone(diff.replace)
            self.assertIsNone(diff.update)
            self.assertIsNone(diff.remove)
            self.assertIsNone(diff.append)
            self.assertEquals(f, diff.apply(f))

    def test_diff_numbers(self):
        a = 4
        b = 7
        diff = Diff(a, b)
        self.assertEquals(7, diff.replace)
        self.assertEquals(b, diff.apply(a))

    def test_diff_strings(self):
        a = 'foo'
        b = 'bar'
        diff = Diff(a, b)
        self.assertEquals('bar', diff.replace)
        self.assertEquals(b, diff.apply(a))

    def test_diff_array_append(self):
        a = ['foo']
        b = ['foo', 'bar']
        diff = Diff(a, b)
        self.assertEquals({1: 'bar'}, diff.append)
        self.assertEquals(b, diff.apply(a))

    def test_diff_array_update(self):
        a = ['foo', 'bar']
        b = ['foo', 'baz']
        diff = Diff(a, b)
        self.assertEquals({1: 'baz'}, diff.update)
        self.assertEquals(b, diff.apply(a))

    def test_diff_array_remove(self):
        a = ['foo', 'bar']
        b = ['foo']
        diff = Diff(a, b)
        self.assertEquals({1: 'bar'}, diff.remove)
        self.assertEquals(b, diff.apply(a))

    def test_diff_array_nested_append(self):
        a = ['foo', ['bar']]
        b = ['foo', ['bar', 'baz']]
        diff = Diff(a, b)
        self.assertEquals({1: 'baz'}, diff.update[1].append)
        self.assertEquals(b, diff.apply(a))

    def test_diff_array_nested_update(self):
        a = ['foo', ['bar', 'baz']]
        b = ['foo', ['bar', 'bazzz']]
        diff = Diff(a, b)
        self.assertEquals({1: 'bazzz'}, diff.update[1].update)
        self.assertEquals(b, diff.apply(a))

    def test_diff_array_nested_remove(self):
        a = ['foo', ['bar', 'baz']]
        b = ['foo', ['bar']]
        diff = Diff(a, b)
        self.assertEquals({1: 'baz'}, diff.update[1].remove)
        self.assertEquals(b, diff.apply(a))

    def test_diff_dict_append(self):
        a = {'roses': 'red'}
        b = {'roses': 'red', 'violets': 'blue'}
        diff = Diff(a, b)
        self.assertEquals({'violets': 'blue'}, diff.append)
        self.assertEquals(b, diff.apply(a))

    def test_diff_dict_update(self):
        a = {'roses': 'red', 'violets': 'blue'}
        b = {'roses': 'red', 'violets': 'aqua'}
        diff = Diff(a, b)
        self.assertEquals({'violets': 'aqua'}, diff.update)
        self.assertEquals(b, diff.apply(a))

    def test_diff_dict_remove(self):
        a = {'roses': 'red', 'violets': 'blue'}
        b = {'roses': 'red'}
        diff = Diff(a, b)
        self.assertEquals({'violets': 'blue'}, diff.remove)
        self.assertEquals(b, diff.apply(a))

    def test_diff_dict_nested_append(self):
        a = {'flowers': {'roses': 'red'}}
        b = {'flowers': {'roses': 'red', 'violets': 'blue'}}
        diff = Diff(a, b)
        self.assertEquals({'violets': 'blue'}, diff.update['flowers'].append)
        self.assertEquals(b, diff.apply(a))

    def test_diff_dict_nested_update(self):
        a = {'flowers': {'roses': 'red', 'violets': 'blue'}}
        b = {'flowers': {'roses': 'red', 'violets': 'aqua'}}
        diff = Diff(a, b)
        self.assertEquals({'violets': 'aqua'}, diff.update['flowers'].update)
        self.assertEquals(b, diff.apply(a))

    def test_diff_dict_nested_remove(self):
        a = {'flowers': {'roses': 'red', 'violets': 'blue'}}
        b = {'flowers': {'roses': 'red'}}
        diff = Diff(a, b)
        self.assertEquals({'violets': 'blue'}, diff.update['flowers'].remove)
        self.assertEquals(b, diff.apply(a))

    def test_diff_scalar_replace_no_conflict(self):
        a = 'foo'
        b = 'bar'
        c = 'bar'
        conflict = Conflict(Diff(a, b), Diff(a, c))
        self.assertFalse(conflict)

    def test_diff_scalar_replace_conflict(self):
        a = 'foo'
        b = 'bar'
        c = 'baz'
        conflict = Conflict(Diff(a, b), Diff(a, c))
        self.assertEquals(('bar', 'baz'), conflict.replace)

    def test_diff_array_append_conflict(self):
        a = ['foo']
        b = ['foo', 'bar']
        c = ['foo', 'baz']
        conflict = Conflict(Diff(a, b), Diff(a, c))
        # self.assertEquals(('bar', 'baz'), conflict[1].append)
        self.assertEquals({1: ('bar', 'baz')}, conflict.append)

    def test_diff_array_update_conflict(self):
        a = ['foo', 'bar']
        b = ['foo', 'baz']
        c = ['foo', 'bazzz']
        conflict = Conflict(Diff(a, b), Diff(a, c))
        # self.assertEquals(('baz', 'bazzz'), conflict[1].update)
        self.assertEquals({1: ('baz', 'bazzz')}, conflict.update)

    def test_diff_array_remove_conflict(self):
        a = ['foo', 'bar']
        b = ['foo', 'baz']
        c = ['foo']
        conflict = Conflict(Diff(a, b), Diff(a, c))
        # self.assertEquals(('baz', None), conflict[1].update)
        # self.assertEquals((None, 'bar'), conflict[1].remove)
        self.assertEquals({1: ('baz', None)}, conflict.update)
        self.assertEquals({1: (None, 'bar')}, conflict.remove)

    def test_diff_dict_append_conflict(self):
        a = {'roses': 'red'}
        b = {'roses': 'red', 'violets': 'blue'}
        c = {'roses': 'red', 'violets': 'magenta'}
        conflict = Conflict(Diff(a, b), Diff(a, c))
        self.assertEquals({'violets': ('blue', 'magenta')}, conflict.append)

# -*- coding: utf-8 -*-

from jsongit.models import Diff
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
            self.assertEquals(b, diff.replace, msg="%s vs. %s" % (a, b))

    def test_no_changes(self):
        for f in self.fixtures:
            diff = Diff(f, f)
            self.assertIsNone(diff.replace)
            self.assertIsNone(diff.update)
            self.assertIsNone(diff.remove)
            self.assertIsNone(diff.append)

    def test_diff_numbers(self):
        diff = Diff(4,
                    7)
        self.assertEquals(7, diff.replace)

    def test_diff_strings(self):
        diff = Diff('foo',
                    'bar')
        self.assertEquals('bar', diff.replace)

    def test_diff_array_append(self):
        diff = Diff(['foo'],
                    ['foo', 'bar'])
        self.assertEquals({1: 'bar'}, diff.append)

    def test_diff_array_update(self):
        diff = Diff(['foo', 'bar'],
                    ['foo', 'baz'])
        self.assertEquals({1: 'baz'}, diff.update)

    def test_diff_array_remove(self):
        diff = Diff(['foo', 'bar'],
                    ['foo'])
        self.assertEquals({1: 'bar'}, diff.remove)

    def test_diff_array_nested_append(self):
        diff = Diff(['foo', ['bar']],
                    ['foo', ['bar', 'baz']])
        self.assertEquals({1: 'baz'}, diff.update[1].append)

    def test_diff_array_nested_update(self):
        diff = Diff(['foo', ['bar', 'baz']],
                    ['foo', ['bar', 'bazzz']])
        self.assertEquals({1: 'bazzz'}, diff.update[1].update)

    def test_diff_array_nested_remove(self):
        diff = Diff(['foo', ['bar', 'baz']],
                    ['foo', ['bar']])
        self.assertEquals({1: 'baz'}, diff.update[1].remove)

    def test_diff_dict_append(self):
        diff = Diff({'roses': 'red'},
                    {'roses': 'red', 'violets': 'blue'})
        self.assertEquals({'violets': 'blue'}, diff.append)

    def test_diff_dict_update(self):
        diff = Diff({'roses': 'red', 'violets': 'blue'},
                    {'roses': 'red', 'violets': 'aqua'})
        self.assertEquals({'violets': 'aqua'}, diff.update)

    def test_diff_dict_remove(self):
        diff = Diff({'roses': 'red', 'violets': 'blue'},
                    {'roses': 'red'})
        self.assertEquals({'violets': 'blue'}, diff.remove)

    def test_diff_dict_nested_append(self):
        diff = Diff({'flowers': {'roses': 'red'}},
                    {'flowers': {'roses': 'red', 'violets': 'blue'}})
        self.assertEquals({'violets': 'blue'}, diff.update['flowers'].append)

    def test_diff_dict_nested_update(self):
        diff = Diff({'flowers': {'roses': 'red', 'violets': 'blue'}},
                    {'flowers': {'roses': 'red', 'violets': 'aqua'}})
        self.assertEquals({'violets': 'aqua'}, diff.update['flowers'].update)

    def test_diff_dict_nested_remove(self):
        diff = Diff({'flowers': {'roses': 'red', 'violets': 'blue'}},
                    {'flowers': {'roses': 'red'}})
        self.assertEquals({'violets': 'blue'}, diff.update['flowers'].remove)


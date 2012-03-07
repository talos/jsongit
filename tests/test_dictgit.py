"""
Test caustic/dictgit.py .
"""

import os
import unittest
import shutil
from dictgit.dictgit import DictRepository, signature

TEST_DIR = os.path.join('test', 'tmp')

SIG = signature('user', 'user@domain.com')

class TestDictRepository(unittest.TestCase):

    def setUp(self):
        """
        Build a new test dir for each run.
        """
        self.repo = DictRepository(TEST_DIR)

    def tearDown(self):
        """
        Kill the old test dir after each run.
        """
        shutil.rmtree(TEST_DIR)

    def test_new_repo(self):
        """
        Make sure repo exists.
        """
        self.assertTrue(os.path.isdir(TEST_DIR))

    def test_empty_dict(self):
        """
        Arbitrary path should return None.
        """
        self.assertIsNone(self.repo.get('nuthin'))

    def test_commit_non_dict(self):
        """
        Test raises a ValueError.
        """
        for non_dict in ['string', 7, ['foo', 'bar']]:
            with self.assertRaises(ValueError):
                self.repo.commit('path', non_dict, SIG, SIG, 'message')

    def test_commit_get(self):
        """
        Commit to the repo.  Make sure the commit happened.
        """
        data = {'roses': 'red', 'violets': 'blue', 'foo': ['bar', 'baz']}
        self.repo.commit('path', data, SIG, SIG, 'message')
        self.assertEquals(data, self.repo.get('path'))

    def test_multiple_commits(self):
        """
        Make a few commits and make sure we get the most recent content.
        """
        self.repo.commit('path', {'foo':'bar'}, SIG, SIG, 'message')
        self.repo.commit('path', {'foo':'baz'}, SIG, SIG, 'message')
        self.assertEqual({'foo': 'baz'}, self.repo.get('path'))

    def test_clone(self):
        """
        Clone an existing path.
        """
        self.repo.commit('original', {'foo': 'bar'}, SIG, SIG, 'message')
        self.repo.clone('original', 'clone')
        self.assertEqual({'foo': 'bar'}, self.repo.get('clone'))

    def test_clone_nonexistent(self):
        """
        Cloning nonexistent path should throw KeyError.
        """
        with self.assertRaises(KeyError):
            self.repo.clone('nonexistent', 'clone')

    def test_clone_already_existing(self):
        """
        Cloning already extant path should throw ValueError.
        """
        self.repo.commit('foo', {'foo': 'bar'}, SIG, SIG, 'message')
        self.repo.commit('bar', {'foo': 'bar'}, SIG, SIG, 'message')
        with self.assertRaises(ValueError):
            self.repo.clone('foo', 'bar')

    def test_clone_self(self):
        """
        Cloning existing repo should throw a ValueError.
        """
        self.repo.commit('foo', {'foo': 'bar'}, SIG, SIG, 'message')
        with self.assertRaises(ValueError):
            self.repo.clone('foo', 'foo')

    def test_nonshared_merge(self):
        """
        Cannot merge if no shared parent commit.
        """
        self.repo.commit('foo', {'roses': 'red'}, SIG, SIG, 'message')
        self.repo.commit('bar', {'violets': 'blue'}, SIG, SIG, 'message')
        self.assertFalse(self.repo.merge('foo', 'bar', SIG, SIG))

    def test_fast_forward_merge(self):
        """
        If there are no intervening commits, this merge should be simple.
        """
        self.repo.commit('foo', {}, SIG, SIG, 'message')
        self.repo.clone('foo', 'bar')
        self.repo.commit('foo', {'roses': 'red'}, SIG, SIG, 'message')
        self.assertTrue(self.repo.merge('foo', 'bar', SIG, SIG))
        self.assertEqual({'roses': 'red'}, self.repo.get('bar'))

    def test_merge_conflict(self):
        """
        If there was a conflict that cannot be automatically resolved, should
        not merge.
        """
        self.repo.commit('foo', {'roses': 'red'}, SIG, SIG, 'message')
        self.repo.clone('foo', 'bar')
        self.repo.commit('foo', {'roses': 'pink'}, SIG, SIG, 'message')
        self.repo.commit('bar', {'roses': 'orange'}, SIG, SIG, 'message')
        self.assertFalse(self.repo.merge('foo', 'bar', SIG, SIG))

    def test_automatic_merge(self):
        """
        If the changes don't conflict, merges should be automatic.
        """
        self.repo.commit('foo', {'roses': 'red'}, SIG, SIG, 'message')
        self.repo.clone('foo', 'bar')
        self.repo.commit('foo', {'roses': 'red',
                                 'violets': 'blue'}, SIG, SIG, 'message')
        self.repo.commit('bar', {'roses': 'red',
                                 'lilacs': 'purple'}, SIG, SIG, 'message')
        self.assertTrue(self.repo.merge('foo', 'bar', SIG, SIG))
        self.assertEquals({'roses':'red',
                           'violets':'blue',
                           'lilacs': 'purple'}, self.repo.get('bar'))

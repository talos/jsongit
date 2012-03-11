import os
from helpers import RepoTestCase, REPO_DIR

class TestJsonGitRepository(RepoTestCase):

    def test_new_repo(self):
        """
        Make sure repo exists.
        """
        self.assertTrue(os.path.isdir(REPO_DIR))

    def test_has(self):
        """
        Test existence of extant key
        """
        self.repo.create('foo', {'roses': 'red'})
        self.assertTrue(self.repo.has('foo'))

    def test_does_not_have(self):
        """
        Test existence of nonexistent key
        """
        self.assertFalse(self.repo.has('foo'))

    def test_get_nonexistent(self):
        """
        Arbitrary path should cause KeyError
        """
        with self.assertRaises(KeyError):
            self.assertEqual({}, self.repo.get('nuthin'))

    def test_create_number(self):
        """Support numbers.
        """
        self.repo.create('number', 7)
        self.assertEqual(7, self.repo.get('number').value)

    def test_create_string(self):
        """Support strings
        """
        self.repo.create('string', 'foo bar baz')
        self.assertEqual('foo bar baz', self.repo.get('string').value)

    def test_create_list(self):
        """Support lists
        """
        self.repo.create('list', ['foo', 'bar', 'baz'])
        self.assertEqual(['foo', 'bar', 'baz'], self.repo.get('list').value)

    def test_create_dict(self):
        """Support dicts
        """
        self.repo.create('dict', {'foo': 'bar'})
        self.assertEqual({'foo': 'bar'}, self.repo.get('dict').value)

    def test_clone(self):
        """
        Clone an existing GitDict
        """
        foo = self.repo.create('foo', {'roses': 'red'})
        bar = self.repo.clone(foo, 'bar')
        self.assertEqual('bar', bar.key)
        self.assertEqual(dict({'roses': 'red'}), bar)

    def test_clone_already_existing(self):
        """
        Cloning already extant key should throw ValueError.
        """
        foo = self.repo.create('foo', {'roses': 'red'})
        self.repo.create('bar', {'violets': 'blue'})
        with self.assertRaises(ValueError):
            self.repo.clone(foo, 'bar')

    def test_clone_self(self):
        """
        Cloning existing key should throw a ValueError.
        """
        foo = self.repo.create('foo', {'roses': 'red'})
        with self.assertRaises(ValueError):
            self.repo.clone(foo, 'foo')


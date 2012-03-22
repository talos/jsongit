import jsongit
import helpers
import os
import json
import pygit2
import shutil

class TestJsonGitRepository(helpers.RepoTestCase):

    def test_create_path_arg(self):
        repo = jsongit.init('test_create_repo')
        self.assertTrue(os.path.isdir('test_create_repo'))
        repo.destroy()

    def test_create_path_kwarg(self):
        repo = jsongit.init(path='test_create_repo_kwarg')
        self.assertTrue(os.path.isdir('test_create_repo_kwarg'))
        repo.destroy()

    def test_destroy_repo(self):
        repo = jsongit.init('test_destroy_repo')
        repo.destroy()
        self.assertFalse(os.path.isdir('test_destroy_repo'))

    def test_has(self):
        """
        Test existence of extant key
        """
        self.repo.commit('foo', {'roses': 'red'})
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
            self.assertEqual({}, self.repo.get('nuthin').value)

    def test_commit_number(self):
        """Support numbers.
        """
        self.repo.commit('number', 7)
        self.assertEqual(7, self.repo.get('number').value)

    def test_commit_string(self):
        """Support strings
        """
        self.repo.commit('string', 'foo bar baz')
        self.assertEqual('foo bar baz', self.repo.get('string').value)

    def test_commit_list(self):
        """Support lists
        """
        self.repo.commit('list', ['foo', 'bar', 'baz'])
        self.assertEqual(['foo', 'bar', 'baz'], self.repo.get('list').value)

    def test_commit_dict(self):
        """Support dicts
        """
        self.repo.commit('dict', {'foo': 'bar'})
        self.assertEqual({'foo': 'bar'}, self.repo.get('dict').value)

    def test_commit_info(self):
        """Get head and info
        """
        self.repo.commit('obj', {'foo': 'bar'},
                         message='my special message',
                         author=jsongit.utils.signature('sally', 's@s.com'))
        commit = self.repo.get('obj')
        self.assertEquals('my special message', commit.message)
        self.assertEquals('sally', commit.author.name)
        self.assertEquals('s@s.com', commit.author.email)

    def test_get_back(self):
        """Get historical head and info
        """
        self.repo.commit('obj', {'foo': 'bar'},
                         message='my special message',
                         author=jsongit.utils.signature('sally', 's@s.com'))
        self.repo.commit('obj', {'bar': 'baz'})
        commit = self.repo.get('obj', back=1)
        self.assertEquals({'foo': 'bar'}, commit.value)
        self.assertEquals('my special message', commit.message)
        self.assertEquals('sally', commit.author.name)
        self.assertEquals('s@s.com', commit.author.email)

    def test_head_back_too_far(self):
        """Should get IndexError if we try to go back too far.
        """
        self.repo.commit('obj', {'foo': 'bar'})
        self.repo.commit('obj', {'bar': 'baz'})
        with self.assertRaises(IndexError):
            self.repo.get('obj', back=2)

    def test_merge_nonexistent(self):
        """ Merging nonexistent throws a KeyError.
        """
        self.repo.commit('foo', {'roses': 'red'})
        with self.assertRaises(KeyError):
            self.repo.merge('bar', 'foo')

    def test_fork_new_key(self):
        """ Fork to create a new key.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.fork('bar', 'foo')
        self.assertEqual({'roses': 'red'}, self.repo.get('bar').value)

    def test_fork_commit(self):
        """Explicitly fork a commit.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.fork('bar', commit=self.repo.get('foo'))
        self.assertEqual({'roses': 'red'}, self.repo.get('bar').value)

    def test_fork_old(self):
        """Explicitly fork from an older commit.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.commit('foo', {'violets': 'blue'})
        self.repo.fork('bar', commit=self.repo.get('foo', back=1))
        self.assertEqual({'roses': 'red'}, self.repo.get('bar').value)

    def test_merge_already_existing(self):
        """
        Merge should not overwrite independent already existing value.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.commit('bar', {'violets': 'blue'})
        self.repo.merge('bar', 'foo')
        self.assertEqual({'violets': 'blue'}, self.repo.get('bar').value)

    def test_merge_self(self):
        """
        Merging identical keys should raise an error.
        """
        self.repo.commit('foo', {'roses': 'red'})
        with self.assertRaises(ValueError):
            self.repo.merge('foo', 'foo')

    def test_commit_updating(self):
        """
        Can use commit to update.
        """
        self.repo.commit('foo', {'roses':'red'})
        self.repo.commit('foo', {})
        self.assertEqual({}, self.repo.get('foo').value)

    def test_not_json(self):
        """
        Cannot commit something that cannot be converted to JSON to the db.
        """
        not_json = [lambda x: x]
        for item in not_json:
            with self.assertRaises(jsongit.NotJsonError):
                self.repo.commit('foo', item)

    def test_key_must_be_string(self):
        """
        Cannot commit to a non-string key in the repo.
        """
        not_strings = [lambda x: x, 4, None, ['foo', 'bar'], {'foo': 'bar'}]
        for item in not_strings:
            with self.assertRaises(jsongit.InvalidKeyError):
                self.repo.commit(item, {'foo': 'bar'})

    def test_all_keys_in_master(self):
        """All keys should be real blobs in the repo's head.
        """
        self.repo.commit('roses', 'red')
        self.repo.commit('violets', 'blue')

        pygit2_repo = self.repo._repo
        head_ref = pygit2_repo.lookup_reference('HEAD').resolve()
        head_commit = pygit2_repo[head_ref.oid]
        tree = head_commit.tree
        self.assertIn('roses', tree)
        self.assertIn('violets', tree)
        self.assertEquals(json.dumps('red'), tree['roses'].to_object().data)
        self.assertEquals(json.dumps('blue'), tree['violets'].to_object().data)

    def test_overlapping_paths(self):
        """Should throw error if key overlaps with directory.
        """
        self.repo.commit('path/to', 'foo')
        with self.assertRaises(jsongit.InvalidKeyError):
            self.repo.commit('path/to/key', 'bar')

    def test_optional_absolute(self):
        """Absolute-ish path should make no difference.
        """
        self.repo.commit('/absolute', 'foo')
        self.assertEquals('foo', self.repo.get('/absolute').value)
        self.assertEquals('foo', self.repo.get('absolute').value)

    def test_no_directory_path(self):
        """Should not be able to store data in a directory.
        """
        with self.assertRaises(jsongit.InvalidKeyError):
            self.repo.commit('path/to/directory/', 'foo')

    def xtest_nonbare_repo_master_tree(self):
        """Should be able to work with an existing non-bare repo.  Commits
        should appear as standard blobs in the master tree.
        """
        PATH = 'nonbare'
        if os.path.lexists(PATH):
            self.fail("Cannot run test, something exists at %s" % PATH)

        try:
            nonbare = pygit2.init_repository(PATH, False)

            repo = jsongit.init(repo=nonbare)
            repo.commit('foo', 'bar')
            repo.commit('path/to/file.json', {'roses': 'red', 'violets': 'blue'})

            # equivalent to checkout master
            head = nonbare.lookup_reference('HEAD').resolve()
            # index = nonbare.index
            # index.read_tree(nonbare[head.oid].tree.oid)
            # index.write()
        finally:
            shutil.rmtree(PATH)

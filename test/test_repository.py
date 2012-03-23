import jsongit
import helpers
import os
import json
# import pygit2
# import shutil

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

    def test_add_is_staged(self):
        """
        Adding a key should stage it to the index.
        """
        self.repo.add('foo', {'roses': 'red'})
        self.assertTrue(self.repo.staged('foo'))
        self.assertEqual({'roses':'red'}, self.repo.index('foo'))

    def test_add_is_not_committed(self):
        """
        An added key is not committed, though.
        """
        self.repo.add('foo', 'bar')
        self.assertFalse(self.repo.committed('foo'))

    def test_add(self):
        """
        Since adding doesn't commit, so we can't show.
        """
        self.repo.add('foo', 'bar')
        with self.assertRaises(KeyError):
            self.repo.show('foo')

    def test_nonexistent_not_staged_or_committed(self):
        """
        Nonexistent keys are neither staged nor committed.
        """
        self.assertFalse(self.repo.staged('foo'))
        self.assertFalse(self.repo.committed('foo'))

    def test_show_nonexistent(self):
        """
        Arbitrary path should cause KeyError
        """
        with self.assertRaises(KeyError):
            self.assertEqual({}, self.repo.show('nuthin'))


    def test_add_then_commit(self):
        """
        Can add, then commit in separate step.
        """
        self.repo.add('foo', 'bar')
        self.repo.commit()
        self.assertEquals('bar', self.repo.show('foo'))
        self.assertFalse(self.repo.staged('foo'))
        self.assertTrue(self.repo.committed('foo'))

    def test_add_multiple_then_commit(self):
        """
        Can add several items and commit them all.
        """
        self.repo.add('roses', 'red')
        self.repo.add('violets', 'blue')
        self.repo.commit()
        self.assertEquals('red', self.repo.show('roses'))
        self.assertEquals('blue', self.repo.show('violets'))

    def test_commit_single_key(self):
        """
        Can add several keys and only commit one.
        """
        self.repo.add('roses', 'red')
        self.repo.add('violets', 'blue')
        self.repo.commit('roses')
        self.assertEquals('red', self.repo.show('roses'))
        self.assertTrue(self.repo.staged('violets'))
        self.assertFalse(self.repo.committed('violets'))

    def test_convenient_commit(self):
        """
        Can add and commit simultaneously.
        """
        self.repo.commit('foo', 'bar')
        self.assertEqual('bar', self.repo.show('foo'))

    def test_commit_number(self):
        """Support numbers.
        """
        self.repo.commit('number', 7)
        self.assertEqual(7, self.repo.show('number'))

    def test_commit_string(self):
        """Support strings
        """
        self.repo.commit('string', 'foo bar baz')
        self.assertEqual('foo bar baz', self.repo.show('string'))

    def test_commit_list(self):
        """Support lists
        """
        self.repo.commit('list', ['foo', 'bar', 'baz'])
        self.assertEqual(['foo', 'bar', 'baz'], self.repo.show('list'))

    def test_commit_dict(self):
        """Support dicts
        """
        self.repo.commit('dict', {'foo': 'bar'})
        self.assertEqual({'foo': 'bar'}, self.repo.show('dict'))

    def test_shows_committed(self):
        """
        Should show from HEAD, not from a more recently added value.
        """
        self.repo.commit("foo", 'committed')
        self.repo.add('foo', 'added')
        self.assertEqual('committed', self.repo.show('foo'))

    def test_head(self):
        """Get head and info
        """
        self.repo.commit('obj', {'foo': 'bar'},
                         message='my special message',
                         author=jsongit.utils.signature('sally', 's@s.com'))
        commit = self.repo.head('obj')
        self.assertEquals('my special message', commit.message)
        self.assertEquals('sally', commit.author.name)
        self.assertEquals('s@s.com', commit.author.email)

    def test_show_old(self):
        """Show old data.
        """
        self.repo.commit('foo', 'step 1')
        self.repo.commit('foo', 'step 2')
        self.assertEqual('step 1', self.repo.show('foo', back=1))

    def test_head_back_too_far(self):
        """Should get IndexError if we try to go back too far.
        """
        self.repo.commit('obj', {'foo': 'bar'})
        self.repo.commit('obj', {'bar': 'baz'})
        with self.assertRaises(IndexError):
            self.repo.show('obj', back=2)

    def test_merge_nonexistent(self):
        """ Merging nonexistent throws a KeyError.
        """
        self.repo.commit('foo', {'roses': 'red'})
        with self.assertRaises(KeyError):
            self.repo.merge('bar', 'foo')

    def test_checkout_new_key(self):
        """Checkout can create a new key.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.checkout('foo', 'bar')
        self.assertEqual({'roses': 'red'}, self.repo.show('bar'))

    # def test_checkout_old(self):
    #     """Explicitly checkout from an older commit.
    #     """
    #     self.repo.commit('foo', {'roses': 'red'})
    #     self.repo.commit('foo', {'violets': 'blue'})
    #     self.repo.fork('bar', commit=self.repo.get('foo', back=1))
    #     self.assertEqual({'roses': 'red'}, self.repo.get('bar').value)

    def test_merge_already_existing(self):
        """
        Merge should not overwrite independent already existing value.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.commit('bar', {'violets': 'blue'})
        self.repo.merge('bar', 'foo')
        self.assertEqual({'violets': 'blue'}, self.repo.show('bar'))

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
        self.assertEqual({}, self.repo.show('foo'))

    def test_not_json(self):
        """
        Cannot add or commit something that cannot be converted to JSON to the db.
        """
        not_json = [lambda x: x, type(object), object(), json]
        for item in not_json:
            with self.assertRaises(jsongit.NotJsonError):
                self.repo.add('foo', item)
        for item in not_json:
            with self.assertRaises(jsongit.NotJsonError):
                self.repo.commit('foo', item)

    def test_key_must_be_string(self):
        """
        Cannot add or commit to a non-string key in the repo.
        """
        not_strings = [lambda x: x, 4, None, ['foo', 'bar'], {'foo': 'bar'}]
        for item in not_strings:
            with self.assertRaises(jsongit.InvalidKeyError):
                self.repo.add(item, {'foo': 'bar'})
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

    def test_no_absolute(self):
        """Absolute-ish path is forbidden, because it leads to a mismatch
        between tree entries and the commit name.
        """
        with self.assertRaises(jsongit.InvalidKeyError):
            self.repo.commit('/absolute', 'foo')

    def test_no_directory_path(self):
        """Should not be able to store data in a directory.
        """
        with self.assertRaises(jsongit.InvalidKeyError):
            self.repo.commit('path/to/directory/', 'foo')

   #  def xtest_nonbare_repo_master_tree(self):
   #      """Should be able to work with an existing non-bare repo.  Commits
   #      should appear as standard blobs in the master tree.
   #      """
   #      PATH = 'nonbare'
   #      if os.path.lexists(PATH):
   #          self.fail("Cannot run test, something exists at %s" % PATH)

   #      try:
   #          nonbare = pygit2.init_repository(PATH, False)

   #          repo = jsongit.init(repo=nonbare)
   #          repo.commit('foo', 'bar')
   #          repo.commit('path/to/file.json', {'roses': 'red', 'violets': 'blue'})

   #          # equivalent to checkout master
   #          head = nonbare.lookup_reference('HEAD').resolve()
   #          # index = nonbare.index
   #          # index.read_tree(nonbare[head.oid].tree.oid)
   #          # index.write()
   #      finally:
   #          shutil.rmtree(PATH)


    def test_remove(self):
        """Should be able to remove a key from the repo.
        """
        self.repo.commit('foo', 'bar')
        self.repo.remove('foo')
        self.assertFalse(self.repo.staged('foo'))
        self.assertFalse(self.repo.committed('foo'))
        with self.assertRaises(KeyError):
            self.repo.show('foo')

    def test_removed_commit(self):
        """If we have a reference to a removed commit, should still be able to
        work with it.
        """
        self.repo.commit('foo', 'bar')
        commit = self.repo.head('foo')
        self.repo.remove('foo')
        self.assertEqual('bar', commit.data)

    def test_remove_stated_raises(self):
        """We get an exception if we try to remove a key that has uncommitted
        data.
        """
        self.repo.commit('foo', 'bar')
        self.repo.add('foo', 'baz')
        with self.assertRaises(jsongit.StagedDataError):
            self.repo.remove('foo')

    def test_remove_forced(self):
        """If we provide force flag, then the key is removed from the index
        as well.
        """
        self.repo.commit('foo', 'bar')
        self.repo.add('foo', 'baz')
        self.repo.remove('foo', force=True)
        self.assertFalse(self.repo.staged('foo'))
        self.assertFalse(self.repo.committed('foo'))

    # not sure of a compelling use for this.
    # def xtest_keys(self):
    #     """Should provide a generator that can yield all the keys in a repo.
    #     """
    #     self.repo.commit('a', 'foo')
    #     self.repo.commit('b', 'bar')
    #     self.repo.commit('c', 'baz')
    #     keys = self.repo.keys()
    #     self.assertNotIn('len', keys)
    #     self.assertItemsEqual(['a', 'b', 'c'], [key for key in keys])

    def test_log(self):
        """Should provide a generator that tracks through commits.
        """
        self.repo.commit('president', 'washington')
        self.repo.commit('president', 'adams')
        self.repo.commit('president', 'madison')
        log = self.repo.log('president')
        self.assertEqual('madison', log.next().data)
        self.assertEqual('adams', log.next().data)
        self.assertEqual('washington', log.next().data)

    def test_log_excludes_add(self):
        """Log should not include anything not committed.
        """
        self.repo.commit('foo', 'bar')
        self.repo.add('foo', 'baz')
        log = self.repo.log('foo')
        self.assertEqual('bar', log.next().data)

    def test_reset(self):
        """Reset should eliminate added changes since the last commit.
        """
        self.repo.commit('foo', 'committed')
        self.repo.add('foo', 'added')
        self.repo.reset('foo')
        self.assertEquals('committed', self.repo.index('foo'))

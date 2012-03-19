import jsongit
import helpers
import os

class TestJsonGitRepository(helpers.RepoTestCase):

    def test_create_path_arg(self):
        repo = jsongit.repo('test_create_repo')
        self.assertTrue(os.path.isdir('test_create_repo'))
        repo.destroy()

    def test_create_path_kwarg(self):
        repo = jsongit.repo(path='test_create_repo_kwarg')
        self.assertTrue(os.path.isdir('test_create_repo_kwarg'))
        repo.destroy()

    def test_destroy_repo(self):
        repo = jsongit.repo('test_destroy_repo')
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
            self.assertEqual({}, self.repo.get('nuthin'))

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

    def test_head(self):
        """Get head and info
        """
        self.repo.commit('obj', {'foo': 'bar'},
                         message='my special message',
                         author=jsongit.utils.signature('sally', 's@s.com'))
        head = self.repo.head('obj')
        self.assertEquals({'foo': 'bar'}, head.object.value)
        self.assertEquals('my special message', head.message)
        self.assertEquals('sally', head.author.name)
        self.assertEquals('s@s.com', head.author.email)

    def test_head_back(self):
        """Get historical head and info
        """
        self.repo.commit('obj', {'foo': 'bar'},
                         message='my special message',
                         author=jsongit.utils.signature('sally', 's@s.com'))
        self.repo.commit('obj', {'bar': 'baz'})
        head = self.repo.head('obj', back=1)
        self.assertEquals({'foo': 'bar'}, head.object.value)
        self.assertEquals('my special message', head.message)
        self.assertEquals('sally', head.author.name)
        self.assertEquals('s@s.com', head.author.email)

    def test_head_back_too_far(self):
        """Should get IndexError if we try to go back too far.
        """
        self.repo.commit('obj', {'foo': 'bar'})
        self.repo.commit('obj', {'bar': 'baz'})
        with self.assertRaises(IndexError):
            self.repo.head('obj', back=2)

    def test_fast_forward_default(self):
        """ Copy an existing object with default (key) fast forward.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.fast_forward('bar', 'foo')
        self.assertEqual({'roses': 'red'}, self.repo.get('bar'))

    def test_fast_forward_key(self):
        """Fast forward explicitly to a key.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.fast_forward('bar', key='foo')
        self.assertEqual({'roses': 'red'}, self.repo.get('bar'))

    def test_fast_forward_commit(self):
        """Fast forward explicitly to a commit.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.fast_forward('bar', commit=self.repo.head('foo'))
        self.assertEqual({'roses': 'red'}, self.repo.get('bar'))

    def test_fast_forward_commit_old(self):
        """Fast forward explicitly to an older commit.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.commit('foo', {'violets': 'blue'})
        self.repo.fast_forward('bar', commit=self.repo.head('foo', back=1))
        self.assertEqual({'roses': 'red'}, self.repo.get('bar'))

    def test_fast_forward_already_existing(self):
        """
        Fast forwarding should overwrite already existing value.
        """
        self.repo.commit('foo', {'roses': 'red'})
        self.repo.commit('bar', {'violets': 'blue'})
        self.repo.fast_forward('bar', 'foo')
        self.assertEqual({'roses': 'red'}, self.repo.get('bar'))

    def test_clone_self(self):
        """
        Fast forwarding to identical keys should raise an error.
        """
        self.repo.commit('foo', {'roses': 'red'})
        with self.assertRaises(ValueError):
            self.repo.fast_forward('foo', 'foo')

    def test_commit_updating(self):
        """
        Can use commit to update.
        """
        self.repo.commit('foo', {'roses':'red'})
        self.repo.commit('foo', {})
        self.assertEqual({}, self.repo.get('foo'))

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
            with self.assertRaises(jsongit.BadKeyTypeError):
                self.repo.commit(item, {'foo': 'bar'})



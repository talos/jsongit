from helpers import RepoTestCase

class TestGitDict(RepoTestCase):

    def test_dirty(self):
        """Starts clean, then gets dirty.
        """
        dict = self.repo.create('key')
        self.assertFalse(dict.dirty)
        dict['roses'] = 'red'
        self.assertTrue(dict.dirty)
        dict.commit()
        self.assertFalse(dict.dirty)

    def test_autocommit_never_dirty(self):
        """Can't get dirty if autocommit.
        """
        dict = self.repo.create('key', autocommit=True)
        dict['roses'] = 'red'
        self.assertFalse(dict.dirty)

    def test_commit(self):
        """Values shouldn't take until commit.
        """
        dict = self.repo.create('key')
        dict['roses'] = 'red'
        self.assertEqual({}, self.repo.get('key'))
        dict.commit()
        self.assertEqual({'roses': 'red'}, self.repo.get('key'))

    def test_autocommit(self):
        """Values take immediately if autocommit.
        """
        dict = self.repo.create('key', autocommit=True)
        dict['roses'] = 'red'
        self.assertEqual({'roses': 'red'}, self.repo.get('key'))

    def test_nonshared_merge(self):
        """Cannot merge if no shared parent commit.
        """
        foo = self.repo.create('foo', {'roses': 'red'})
        bar = self.repo.create('bar', {'violets': 'blue'})
        self.assertFalse(foo.merge(bar))
        self.assertFalse(bar.merge(foo))

    def test_fast_forward_merge(self):
        """If there are no intervening commits, this merge should be simple.
        """
        foo = self.repo.create('foo', {'roses': 'red'})
        bar = self.repo.clone(foo, 'bar')
        bar['violets'] = 'blue'
        bar.commit()
        self.assertTrue(foo.merge(bar))
        self.assertEqual({'roses': 'red', 'violets': 'blue'}, dict(bar))

    def test_merge_conflict(self):
        """
        If there was a conflict that cannot be automatically resolved, should
        not merge.
        """
        foo = self.repo.create('foo', {'roses': 'red'})
        bar = self.repo.create('bar', {'roses': 'red'})
        foo['roses'] = 'pink'
        foo.commit()
        bar['roses'] = 'orange'
        bar.commit()
        self.assertFalse(foo.merge(bar))
        self.assertFalse(bar.merge(foo))

    def test_automatic_merge(self):
        """
        If the changes don't conflict, merges should be automatic.
        """
        foo = self.repo.create('foo', {'roses': 'red'})
        bar = self.repo.create('bar', {'roses': 'red'})

        foo['violets'] = 'blue'
        foo.commit()

        bar['lilacs'] = 'purple'
        bar.commit()

        self.assertTrue(foo.merge(bar))
        self.assertEqual({'roses':'red',
                          'violets':'blue',
                          'lilacs': 'purple'}, dict(foo))

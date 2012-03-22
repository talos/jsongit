from helpers import RepoTestCase

class TestObject(RepoTestCase):

    def test_dirty(self):
        """Starts clean, then gets dirty.
        """
        dict = self.repo.commit('key', {})
        self.assertFalse(dict.dirty)
        dict['roses'] = 'red'
        self.assertTrue(dict.dirty)
        dict.commit()
        self.assertFalse(dict.dirty)

    def test_autocommit_never_dirty(self):
        """Can't get dirty if autocommit.
        """
        dict = self.repo.commit('key', {}, autocommit=True)
        dict['roses'] = 'red'
        self.assertFalse(dict.dirty)

    def test_commit(self):
        """Values shouldn't take until commit.
        """
        dict = self.repo.commit('key', {})
        dict['roses'] = 'red'
        self.assertEqual({}, self.repo.get('key').value)
        dict.commit()
        self.assertEqual({'roses': 'red'}, self.repo.get('key').value)

    def test_autocommit(self):
        """Values take immediately if autocommit.
        """
        dict = self.repo.commit('key', {}, autocommit=True)
        dict['roses'] = 'red'
        self.assertEqual({'roses': 'red'}, self.repo.get('key').value)

    def test_nonshared_merge(self):
        """Cannot merge if no shared parent commit.
        """
        foo = self.repo.commit('foo', {'roses': 'red'})
        bar = self.repo.commit('bar', {'violets': 'blue'})
        self.assertFalse(foo.merge(bar).success)
        self.assertFalse(bar.merge(foo).success)

    def test_simple_merge(self):
        """If there's a shared parent and no intervening commits, should
        merge.
        """
        foo = self.repo.commit('foo', {'roses': 'red'})
        bar = self.repo.fork('bar', 'foo')
        foo['violets'] = 'blue'
        foo.commit()
        merge = bar.merge(foo)
        self.assertTrue(merge.success)
        self.assertEqual({'roses': 'red', 'violets': 'blue'}, bar.value)

    def test_merge_conflict(self):
        """
        If there was a conflict that cannot be automatically resolved, should
        not merge.
        """
        foo = self.repo.commit('foo', {'roses': 'red'})
        bar = self.repo.fork('bar', 'foo')
        foo['roses'] = 'pink'
        foo.commit()
        bar['roses'] = 'orange'
        bar.commit()
        self.assertFalse(foo.merge(bar).success)
        self.assertFalse(bar.merge(foo).success)

    def test_automatic_merge(self):
        """
        If the changes don't conflict, merges should be automatic.
        """
        foo = self.repo.commit('foo', {'roses': 'red'})
        bar = self.repo.fork('bar', 'foo')

        foo['violets'] = 'blue'
        foo.commit()

        bar['lilacs'] = 'purple'
        bar.commit()

        merge = foo.merge(bar)
        self.assertTrue(merge.success)
        self.assertEqual({'roses':'red',
                          'violets':'blue',
                          'lilacs': 'purple'}, foo.value)

from helpers import RepoTestCase

import jsongit

class TestHistory(RepoTestCase):

    def test_no_history(self):
        """Starts with just the most recent step.
        """
        self.repo.commit('fresh', {'foo': 'bar'})
        gen = self.repo.walk('fresh')
        commit = gen.next()
        self.assertEquals(commit, self.repo.get('fresh').head)
        self.assertEquals(commit.data, self.repo.get('fresh'))

    def test_default_walk(self):
        """Should step through commits backwards all the way by default.
        """
        self.repo.commit('foo', 'step 1')
        self.repo.commit('foo', 'step 2')
        self.repo.commit('foo', 'step 3')
        self.repo.commit('foo', 'step 4')

        gen = self.repo.walk('foo')

        self.assertEquals('step 4', gen.next().data)
        self.assertEquals('step 3', gen.next().data)
        self.assertEquals('step 2', gen.next().data)
        self.assertEquals('step 1', gen.next().data)
        with self.assertRaises(StopIteration):
            gen.next()

    def test_forwards_walk(self):
        """Can specify a forwards walk.
        """
        self.repo.commit('foo', 'step 1')
        self.repo.commit('foo', 'step 2')
        self.repo.commit('foo', 'step 3')
        self.repo.commit('foo', 'step 4')

        gen = self.repo.walk('foo', order=jsongit.GIT_SORT_REVERSE)

        self.assertEquals('step 1', gen.next().data)
        self.assertEquals('step 2', gen.next().data)
        self.assertEquals('step 3', gen.next().data)
        self.assertEquals('step 4', gen.next().data)
        with self.assertRaises(StopIteration):
            gen.next()

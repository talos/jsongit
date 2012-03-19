from helpers import RepoTestCase

import jsongit

class TestLog(RepoTestCase):

    def test_no_log(self):
        """Starts with just the most recent step.
        """
        self.repo.commit('fresh', {'foo': 'bar'})
        gen = self.repo.log('fresh')
        commit = gen.next()
        self.assertEquals(commit, self.repo.get('fresh').head)
        self.assertEquals(commit.object.value, self.repo.get('fresh').value)

    def test_default_log(self):
        """Should step through commits backwards all the way by default.
        """
        self.repo.commit('foo', 'step 1')
        self.repo.commit('foo', 'step 2')
        self.repo.commit('foo', 'step 3')
        self.repo.commit('foo', 'step 4')

        gen = self.repo.log('foo')

        self.assertEquals('step 4', gen.next().object.value)
        self.assertEquals('step 3', gen.next().object.value)
        self.assertEquals('step 2', gen.next().object.value)
        self.assertEquals('step 1', gen.next().object.value)
        with self.assertRaises(StopIteration):
            gen.next()

    def test_reverse_log(self):
        """Can specify a reverse log.
        """
        self.repo.commit('foo', 'step 1')
        self.repo.commit('foo', 'step 2')
        self.repo.commit('foo', 'step 3')
        self.repo.commit('foo', 'step 4')

        gen = self.repo.log('foo', order=jsongit.GIT_SORT_REVERSE)

        self.assertEquals('step 1', gen.next().object.value)
        self.assertEquals('step 2', gen.next().object.value)
        self.assertEquals('step 3', gen.next().object.value)
        self.assertEquals('step 4', gen.next().object.value)
        with self.assertRaises(StopIteration):
            gen.next()

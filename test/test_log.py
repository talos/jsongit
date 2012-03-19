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

    def test_log_messages(self):
        """Retrieves log messages.
        """
        self.repo.commit('foo', 'bar', message="I think this is right.")
        self.repo.commit('foo', 'baz', message="Nope, it was wrong.")

        gen = self.repo.log('foo')

        self.assertEquals("Nope, it was wrong.", gen.next().message)
        self.assertEquals("I think this is right.", gen.next().message)

    def test_log_authors(self):
        """Retrieves authors.
        """
        bob = jsongit.utils.signature('bob', 'bob@bob.com')
        dan = jsongit.utils.signature('dan', 'dan@dan.com')
        self.repo.commit('foo', 'bar', author=bob)
        self.repo.commit('foo', 'baz', author=dan)

        gen = self.repo.log('foo')

        c = gen.next()
        self.assertEquals("dan", c.author.name)
        self.assertEquals("dan@dan.com", c.author.email)
        c = gen.next()
        self.assertEquals("bob", c.author.name)
        self.assertEquals("bob@bob.com", c.author.email)


import sys
import os
if sys.version[:3] < '2.7':
    import unittest2 as unittest
    unittest
else:
    import unittest
import jsongit

PATH = 'test_jsongit_repo'

class RepoTestCase(unittest.TestCase):

    def setUp(self):
        """
        Build a new test dir for each run.
        """
        if os.path.lexists(PATH):
            self.fail("Can't use %s for test repo, something is there." % PATH)
        else:
            self.repo = jsongit.init(path='test_jsongit_repo')

    def tearDown(self):
        """
        Kill the old test dir after each run.
        """
        self.repo.destroy()


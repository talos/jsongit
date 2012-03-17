import sys
import os
if sys.version[:3] < '2.7':
    import unittest2 as unittest
    unittest
else:
    import unittest
import shutil
from jsongit import JsonGitRepository

REPO_DIR = os.path.join('test', 'tmp')

class RepoTestCase(unittest.TestCase):

    def setUp(self):
        """
        Build a new test dir for each run.
        """
        self.repo = JsonGitRepository(REPO_DIR)

    def tearDown(self):
        """
        Kill the old test dir after each run.
        """
        shutil.rmtree(REPO_DIR)


import sys
import os
if sys.version[:3] < '2.7':
    import unittest2 as unittest
    unittest
else:
    import unittest
import shutil
import jsongit
import uuid

class RepoTestCase(unittest.TestCase):

    def new_repo(self, **kwargs):
        return jsongit.repo(**kwargs)

    def setUp(self):
        """
        Build a new test dir for each run.
        """
        self._dir = os.path.join('test', str(uuid.uuid4()))
        self.repo = self.new_repo(path=self._dir)
        self.assertTrue(os.path.isdir(self._dir))

    def tearDown(self):
        """
        Kill the old test dir after each run.
        """
        shutil.rmtree(self._dir)


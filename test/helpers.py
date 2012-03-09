import os
import unittest
import shutil
from gitdict import DictRepository

REPO_DIR = os.path.join('test', 'tmp')

class RepoTestCase(unittest.TestCase):

    def setUp(self):
        """
        Build a new test dir for each run.
        """
        self.repo = DictRepository(REPO_DIR)

    def tearDown(self):
        """
        Kill the old test dir after each run.
        """
        shutil.rmtree(REPO_DIR)


import os
import unittest
import shutil
from gitdict import DictRepository, DictAuthor

REPO_DIR = os.path.join('test', 'tmp')
AUTHOR = DictAuthor('user', 'user@domain.com')

class RepoTestCase(unittest.TestCase):

    def setUp(self):
        """
        Build a new test dir for each run.
        """
        self.repo = DictRepository(REPO_DIR, author=AUTHOR)

    def tearDown(self):
        """
        Kill the old test dir after each run.
        """
        shutil.rmtree(REPO_DIR)


import sys
import helpers
import threading
import random as global_random
import string

FEW = 3
LOTS = 10
MAX_DEPTH = 1

def random_number(r, j, l, min=-sys.maxint, max=sys.maxint):
    r.jumpahead(j + l)
    return r.random() * (max - min) + min

def random_string(r, j, l, min=1, max=50):
    r.jumpahead(j + l)
    return ''.join(r.choice(string.ascii_letters +
                            string.digits)
                   for i in xrange(r.randint(min, max)))

def random_array(r, j, l, min=1, max=10):
    if l > MAX_DEPTH:
        return []
    r.jumpahead(j + l)
    return [random_object(r, i, l + 1) for i in xrange(r.randint(min, max))]

def random_dict(r, j, l, min=1, max=10):
    if l > MAX_DEPTH:
        return {}
    r.jumpahead(j + l)
    return dict([(r.choice([random_string, random_number])(r, i, l),
                  random_object(r, i, l + 1))
                 for i in xrange(r.randint(min, max))])

def random_object(r, j, l):
    r.jumpahead(j + l)
    return r.choice([random_array, random_dict, random_string, random_number])(r, j, l)

def commit(repo, num_commits):
    r = global_random.Random()
    r.seed()
    thread_id = threading.current_thread().ident
    for i in xrange(num_commits):
        repo.commit(random_string(r, thread_id, 0), random_object(r, thread_id, 0))

class TestRepoThreading(helpers.RepoTestCase):

    def do_with_threads(self, size, func, *args):
        """Generate and start size threads with target func.
        """
        pool = [threading.Thread(target=func, args=args) for i in range(size)]
        for thread in pool:
            thread.start()
        return pool

    def join_threads(self, pool):
        for thread in pool:
            thread.join()

    def test_commit_once_few(self):
        """Make one commit each.
        """
        pool = self.do_with_threads(FEW, commit, self.repo, 1)
        self.join_threads(pool)

    def test_commit_once_lots(self):
        """Make one commit each.
        """
        pool = self.do_with_threads(LOTS, commit, self.repo, 1)
        self.join_threads(pool)

    def test_commit_lots_few(self):
        """Make several commits each.
        """
        pool = self.do_with_threads(FEW, commit, self.repo, 10)
        self.join_threads(pool)

    def test_commit_lots_lots(self):
        """Make several commits each.
        """
        pool = self.do_with_threads(LOTS, commit, self.repo, 10)
        self.join_threads(pool)





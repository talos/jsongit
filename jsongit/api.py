# -*- coding: utf-8 -*-

"""
jsongit.api
"""

import os
import pygit2

from .models import Repository
import utils

def init(path=None, repo=None, **kwargs):
    """Obtain a :class:`Repository`.  Either a path to a repo or an
    existing `pygit2.Repository` must be provided.  If the path exists, it will
    be interpreted as the path to an existing repository; if it does not, a new
    bare repository will be created there.

    >>> repo = jsongit.init('path/to/repo')

    Or, if you want to take advantage of special `pygit2` options:

    >>> import pygit2
    >>> pygit_repo = pygit2.init_repository('path/to/repo', False)
    >>> jsongit_repo = jsongit.init(repo=pygit_repo)

    :param path:
        The path to a repository. If it is a path that does not exist, a new
        bare git repository will be initialized there.  If it is a path that
        does exist, then the directory will be used as a repository.
    :type path: string
    :param repo: An existing repository object.
    :type repo: :class:`pygit2.Repository`
    :param dumps:
        (optional) An alternate function to use when dumping data.  Defaults
        to :func:`json.dumps`.
    :type dumps: func
    :param loads:
        (optional) An alternate function to use when loading data.  Defaults
        to :func:`json.loads`.
    :type loads: func

    :returns: A repository reference
    :rtype: :class:`Repository <jsongit.models.Repository>`
    """
    if repo and path:
        raise TypeError("Cannot define repo and path")
    if path:
        if os.path.isdir(path):
            repo = pygit2.Repository(path)
        else:
            bare = kwargs.pop('bare', True) # bare repo by default
            repo = pygit2.init_repository(path, bare)
    if not repo:
        raise TypeError("Missing repo or path")
    dumps = kwargs.pop('dumps', utils.import_json().dumps)
    loads = kwargs.pop('loads', utils.import_json().loads)
    return Repository(repo, dumps, loads)

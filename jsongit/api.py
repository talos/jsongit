# -*- coding: utf-8 -*-

"""
jsongit.api
"""

import os
import pygit2

from .models import Repository
import utils

def repo(path=None, repo=None, **kwargs):
    """Obtain a :class:`Repository`.  Either a path to a repo or an
    existing repo must be provided.

    :param path:
        The path to a repository If it is a path that does not exist, a new
        bare git repository will be initialized there.  If it is a path that
        does exist, then the directory will be used as a bare git repository.
    :type path: string
    :param repo: An existing repository object.
    :type repo: :class:`pygit2.Repository`

    :returns: A repository reference
    :rtype: :class:`jsongit.Repository`
    """
    if repo and path:
        raise TypeError("Cannot define repo and path")
    if path:
        if os.path.isdir(path):
            repo = pygit2.Repository(path)
        else:
            repo = pygit2.init_repository(path, True) # bare repo
    if not repo:
        raise TypeError("Missing repo or path")
    dumps = kwargs.pop('dumps', utils.import_json().dumps)
    loads = kwargs.pop('loads', utils.import_json().loads)
    return Repository(repo, dumps, loads)

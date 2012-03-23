.. jsongit documentation master file, created by
   sphinx-quickstart on Tue Mar  6 23:32:42 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

JsonGit: Git Your Dict
======================

Release v\ |version|. (:ref:`Installation <install>`)

Use git_ as a key-value store to store, track and merge arbitrary data in
Python.

.. _git: http://git-scm.com/

::

    >>> r = jsongit.init('repo')
    >>> r.commit('foo', {})
    >>> r.checkout('foo', 'bar')
    >>> r.commit('foo', {'roses': 'red'})
    >>> r.commit('bar', {'violets': 'blue'})
    >>> r.merge('foo', 'bar').message
    Auto-merge of be92d3dcb6 and dbde44bada from shared parent 5d55214e4f
    >>> r.show('foo')
    {u'roses': u'red', u'violets': u'blue'}
    >>> for commit in r.log('foo'):
    ...     print(commit)
    'foo'='{u'roses': u'red', u'violets': u'blue'}'@fc9e0f3106
    'bar'='{u'violets': u'blue'}'@be92d3dcb6
    'bar'='{}'@5bb29ad7dc
    'foo'='{u'roses': u'red'}'@dbde44bada
    'foo'='{}'@5d55214e4f

JsonGit layers above the Python packages pygit2_ and json_diff_ to give you
logs, merges, diffs, and persistence for any objects that serialize to JSON_.
It's licensed BSD.

.. _pygit2: https://github.com/libgit2/pygit2
.. _json_diff: https://fedorahosted.org/json_diff/
.. _JSON: http://json.org/

Features
--------

- Works with any object that can be serialized as JSON
- Simple key-value store API
- Portable, persistent repositories
- Automatic merging
- Conflict detection
- Key-specific logs and signatures

Usage
-----

Learn how to install and use JsonGit.

.. toctree ::
   :maxdepth: 2

   usage/install
   usage/start

API Documentation
-----------------

The technical nitty-gritty.

.. toctree::
   :maxdepth: 2

   api

.. ---------------------


..  Indices and tables
..  ==================
.. 
..  * :ref:`genindex`
..  * :ref:`modindex`
..  * :ref:`search`


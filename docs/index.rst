.. jsongit documentation master file, created by
   sphinx-quickstart on Tue Mar  6 23:32:42 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

JsonGit: Git Your Dict
======================

Release v\ |version|. (:ref:`Installation <install>`)

Use git_ as a key-value store that stores, tracks and merge arbitrary data in
Python.

.. _git: http://git-scm.com/

::

    >>> r = jsongit.init('repo')
    >>> foo = r.commit('foo', {})
    >>> bar = r.merge('bar', 'foo').result
    >>> foo['roses'] = 'red'
    >>> bar['violets'] = 'blue'
    >>> foo.commit()
    >>> bar.commit()
    >>> foo.merge(bar).message
    u'Auto-merge from ee0badced484570b36bb219ad81567098e9995a7'
    >>> foo.value
    {u'roses': u'red', u'violets': u'blue'}
    >>> log = foo.log()
    >>> pprint([commit.object.value for commit in log])
    [{u'roses': u'red', u'violets': u'blue'},
     {u'violets': u'blue'},
     {},
     {u'roses': u'red'},
     {}]
    ...

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
- Optional object wrapper for lists and dicts
- Portable, persistent repositories
- Automatic merging
- Conflict detection
- Key-specific logs
- Signature support for data

Usage
-----

Learn how to install and use JsonGit.

.. toctree ::
   :maxdepth: 1

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


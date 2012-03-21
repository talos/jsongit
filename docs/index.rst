.. jsongit documentation master file, created by
   sphinx-quickstart on Tue Mar  6 23:32:42 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

JsonGit: Git Your Dict
======================

Release v\ |version|. (:ref:`Installation <install>`)

Use git_ as a key-value store that can track and merge arbitrary data in
Python.

.. git: http://git-scm.com/

::

    >>> r = jsongit.repo('repo')
    >>> foo = r.commit('foo', {'roses': 'red'})
    >>> bar = r.fast_forward('bar', 'foo')
    >>> foo['violets'] = 'blue'
    >>> foo.commit()
    >>> bar['lilacs'] = 'purple'
    >>> bar.commit()
    >>> merge = foo.merge(bar)
    >>> foo.value
    {u'roses': u'red', u'lilacs': u'purple', u'violets': u'blue'}
    >>> merge.message
    u'Auto-merge from dc1ce3d1cc47afd8c5029efccd398d415675d596'
    ...

JsonGit layers above the Python packages pygit2_ and json_diff_ to give you
logs, merges, diffs, and persistence for any objects that serialize to JSON_.
It's licensed BSD.

.. pygit2: https://github.com/libgit2/pygit2
.. json_diff: https://fedorahosted.org/json_diff/
.. JSON: http://json.org/

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

Learn why you would want to use JsonGit, how to install it, and how to use it
with step-by-step guides.

.. toctree ::
   :maxdepth 1:

   usage/why
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


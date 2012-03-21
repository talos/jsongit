.. jsongit documentation master file, created by
   sphinx-quickstart on Tue Mar  6 23:32:42 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

JsonGit: Git Your Dict
======================

Release v\ |version|. (:ref:`Installation <install>`)

Use Git as a key-value store that can track and merge arbitrary data in Python.

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

JsonGit layers above :ref:`pygit2 <https://github.com/libgit2/pygit2>`
and :ref:`json_diff <https://fedorahosted.org/json_diff/>`.

Features
--------

- Stores any data that can be serialized as JSON
- Simple key-value store API
- Optional object wrapper for lists and dicts
- Portable, persistent repositories
- Automatic merging
- Conflict detection
- Signature support for data

API Documentation
-----------------

Docs on classes and methods in jsongit.

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


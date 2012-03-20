.. jsongit documentation master file, created by
   sphinx-quickstart on Tue Mar  6 23:32:42 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

JsonGit: Git Your Dict
======================

Release v\ |version|. (:ref:`Installation <install>`)

JsonGit provides a Python interface to Git as a key-value store that can track
and merge arbitrary data.

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
    ...

API Documentation
-----------------

Docs on all the stuff you could and should use.

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


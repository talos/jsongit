JsonGit
=======

Use Git as a key-value store that can track and merge arbitrary data in Python. 

Installation
------------

JsonGit requires that you have installed
`libgit2 <http://libgit2.github.com/>`_.  You will also need
`pygit2 <https://github.com/libgit2/pygit2>`_ and
`json_diff <https://fedorahosted.org/json_diff/>`_, which are available on
PyPI.

Example
-------

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

Documentation
-------------

Documentation is on `Read the Docs <http://jsongit.readthedocs.org>`_.

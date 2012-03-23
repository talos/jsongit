JsonGit
=======

*git your dict*

Use Git as a key-value store that can track and merge arbitrary data in Python::

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

Installation
------------

Libgit2_ is used to build and modify the git repository. You can find
instructions for installing it here_.

.. _Libgit2: http://libgit2.github.com/
.. _here: http://libgit2.github.com/#install

Pip handles the rest::

    $ pip install jsongit

You can find full installation instructions in the documentation_.

.. _documentation: http://jsongit.readthedocs.org/en/latest/usage/install.html

Documentation
-------------

Documentation is on `Read the Docs`_.

.. _Read the Docs: http://jsongit.readthedocs.org/

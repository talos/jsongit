JsonGit
=======

*git your dict*

Use Git as a key-value store that can track and merge arbitrary data in Python::

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

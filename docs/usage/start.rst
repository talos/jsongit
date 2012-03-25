.. _start:

Getting Started
===============

JsonGit is easy to use and, hopefully, fun.  If you haven't yet, head over to
the :ref:`install <install>` section first.  If you need specific information on
methods or classes, check out the :ref:`api <api>`.

Making a Repo
-------------

You'll need to initialize a repo before storing any data in it::

    >>> repo = jsongit.init('repo')

This creates a new directory in the same directory as you are running your
Python interpreter, and initializes a bare Git repository in it.  Bare git
repositories are equivalent to the `.git` folder of a regular git repo.

Storing data
------------

Now that you've got a repo, you can put data in it::

    >>> repo.add('foo', 'my very special bar')
    >>> repo.commit()

You can commit any python object that will run through :py:func:`json.dumps`.
Strings, ints, floats, booleans, dicts, lists, and None, are all OK::

    >>> repo.add('a', 7)
    >>> repo.add('b', 7.77)
    >>> repo.add('c', True)
    >>> repo.add('d', ['foo', 'bar'])
    >>> repo.add('e', {'roses': 'red'})
    >>> repo.add('f', None)
    >>> repo.commit()

Any combination thereof is kosher, too::

    >>> repo.add('dude', {'job': None, 'age': 42, 'likes': ['bowling', 'rug']})
    >>> repo.commit()

It's oftentimes convenient to add a value and commit simultaneously::

    >>> repo.commit('fast', 'and easy, too!')

This is akin to `git commit -a <file>`.  Until you commit a key, modifications
applied to it via :py:func:`Repository.add` won't be recorded in history.

Retrieving Data
---------------

Pulling the data back out is a matter of retrieving the key's value::

    >>> foo = repo.show('foo')
    u'my very special bar'

The returned object preserves the original type::

    >>> type(repo.show('a'))
    <type 'int'>
    >>> type(repo.show('b'))
    <type 'float'>
    >>> type(repo.show('c'))
    <type 'bool'>
    >>> type(repo.show('d'))
    <type 'list'>
    >>> type(repo.show('e'))
    <type 'dict'>
    >>> type(repo.show('f'))
    <type 'NoneType'>

All data is run back through :py:func:`json.loads` on the way out::

    >>> str(repo.show('dude')['job'])
    'None'
    >>> repo.show('dude')['likes']
    ['bowling', 'rug']

Commit Data
-----------

You can retrieve commit information on a key-by-key basis::

    >>> repo.commit('foo', 'bar', message="leveraging fu")
    >>> commit = repo.head('foo')
    >>> commit.message
    u'leveraging fu'
    >>> commit.author.name
    u'Jon Q. User'
    >>> commit.time
    1332438935L

Merging Data
------------

Keys can be merged back together if they split from a single commit.  First,
checkout an existing key into a new key::

    >>> repo.commit('spoon', {'material': 'silver'})
    >>> repo.checkout('spoon', 'fork')
    >>> repo.show('fork')
    {u'material': u'silver'}

Since `fork` and `spoon` share that initial commit, they can be merged later
on.  Merging returns a :py:class:`Merge` with information about what happened::

    >>> repo.commit('spoon', {'material': 'stainless'})
    >>> merge = repo.merge('fork', 'spoon')
    >>> merge.message
    u'Auto-merge of d0e0aa8061 and ce29b985cf from shared parent d21cb53771'
    >>> repo.show('fork')
    {u'material': u'stainless'}

Intervening changes to `spoon` were applied to `fork`.

Logs
----

All the modifications to a key are available in its log::

    >>> repo.commit('president', 'washington')
    >>> repo.commit('president', 'adams')
    >>> repo.commit('president', 'madison')
    >>> log = repo.log('president')
    >>> for commit in log:
    ...     print(commit.data)
    ...
    madison
    adams
    washington

The :py:func:`Repository.log` method returns a generator that yields
successively deeper commits.

History
-------

By default, :py:func:`Repository.show` returns the data from the most recent
commit.  You can choose to get something from further back on demand::

    >>> repo.show('president', back=2)
    u'washington'

Going too far back in time will raise a friendly reminder::

    >>> repo.show('president', back=300)
    IndexError: president has fewer than 300 commits

Index
-----

Until you actually commit a key, its value is kept in the index::

    >>> repo.add('added', 'but not committed!')
    >>> repo.index('added')
    u'but not committed!'

Since there hasn't been a commit, there's nothing to show::

    >>> repo.show('added')
    KeyError: 'There is no key at added'

Modifications independent of commits won't appear in your log, either::

    >>> repo.add('release', 'pet sounds')
    >>> repo.commit('release')
    >>> repo.add('release', 'smile')
    >>> repo.add('release', 'smiley smile')
    >>> repo.commit('release')
    >>> for commit in repo.log('release'):
    ...    print(commit.data)
    ...
    smiley smile
    pet sounds

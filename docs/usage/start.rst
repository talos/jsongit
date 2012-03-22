.. _start:

Getting Started
===============

JsonGit is easy to use and, hopefully, fun.  If you haven't yet, head over to
the `install <install>` section first.  If you need specific information on
methods or classes, check out the `api <api>`.

Repo Interface
--------------

JsonGit provides two interfaces for modifying and merging your data:

* the repo itself as a key-value store
* wrapped objects

We'll look at the repo interface first.

Making a Repo
~~~~~~~~~~~~~

You'll need to initialize a repo before storing any data in it::

    >>> repo = jsongit.init('repo')

This creates a new directory in the same directory as you are running your
Python interpreter, and initializes a bare Git repository in it.  Bare git
repositories are equivalent to the `.git` folder of a regular git repo.

Storing data
~~~~~~~~~~~~

Now that you've got a repo, you can commit data to it::

    >>> repo.commit('foo', 'my very special bar')

You can commit any python object that will run through :func:`json.dumps`.
Strings, ints, floats, booleans, dicts, lists, None, are all OK::

    >>> repo.commit('a', 7)
    >>> repo.commit('b', 7.77)
    >>> repo.commit('c', True)
    >>> repo.commit('d', ['foo', 'bar'])
    >>> repo.commit('e', {'roses': 'red'})
    >>> repo.commit('f', None)

Any combination thereof is kosher, too::

    >>> repo.commit('dude', {'job': None, 'age': 42, 'likes': ['bowling', 'rug']})

Retrieving Data
~~~~~~~~~~~~~~~

Pulling the data back out is a matter of retrieving the key's value::

    >>> foo = repo.get('foo')
    >>> foo.value
    'my very special bar'

The returned object is wrapped in an :class:`Commit`. The original value
is contained in the :attr:`Commit.value` attribute, which preserves the
original type::

    >>> type(repo.get('a').value)
    <type 'int'>
    >>> type(repo.get('b').value)
    <type 'float'>
    >>> type(repo.get('c').value)
    <type 'bool'>
    >>> type(repo.get('d').value)
    <type 'list'>
    >>> type(repo.get('e').value)
    <type 'dict'>
    >>> type(repo.get('f').value)
    <type 'NoneType'>

All data is run back through :func:`json.loads` on the way out::

    >>> repo.get('dude').value['job']
    None
    >>> repo.get('dude').value['likes']
    ['bowling', 'rug']

Commit Data
~~~~~~~~~~~

The :class:`Commit` also provides information about the commit::

    >>> commit = repo.get('foo')
    >>> commit.message
    'adding foo'
    >>> commit.author.name
    'Jon Q. User'
    >>> commit.time


Merging Data
~~~~~~~~~~~~

Keys can be merged back together if they split from a single commit.  First,
fork an existing commit::

    >>> repo.commit('spoon', {'material': 'silver'})
    >>> repo.fork('fork', 'spoon')
    >>> repo.get('fork').value
    {'material': 'silver'}

Since `fork` and `spoon` share that initial commit, they can be merged later
on.  Merging returns a :class:`Merge` with information about what happened::

    >>> repo.commit('spoon', {'material': 'stainless'})
    >>> merge = repo.merge('fork', 'spoon')
    >>> merge.message

    >>> repo.get('fork').value
    {'material': 'stainless'}

Intervening changes to `spoon` were applied to `fork`.

Logs
~~~~

All the modifications to a key are available in its log::

    >>> repo.commit('president', 'washington')
    >>> repo.commit('president', 'adams')
    >>> repo.commit('president', 'madison')
    >>> log = repo.log('president')
    >>> for commit in log:
    ...     print(commit.value)
    ...
    madison
    adams
    washington

The :func:`Repository.log` method returns a generator that yields successively
deeper commits.

History
~~~~~~~

By default, :func:`Repository.get` returns the most recent commit for a key.
You can choose to get something from further back on demand::

    >>> repo.get('president', back=2).value
    'washington'

Going too far back in time will raise a friendly reminder::

    >>> repo.get('president', back=300).value
    IndexError: president has fewer than 300 commits

.. Wrapped Object Interface
.. ------------------------
.. 
.. While all JsonGit actions can be mapped to methods on the :class:`Repository`,
.. it is often more convenient to keep a reference to a specific key, and call
.. methods upon it instead.
.. 
.. Wrapped objects let you do just that::
.. 
..     >>> wrapped = repo.commit('parappa', {'activity': 'rapper'})
..     >>> wrapped.key
..     'parappa'
..     >>> wrapped.value
..     {'activity': 'rapper'}
..     >>> wrapped['motto'] = 'I gotta believe!'
..     >>> wrapped.commit()
..     >>> repo.get('parappa').value
..     {'motto': 'I gotta believe!', 'activity': 'rapper'}
.. 
.. Iteration
.. ~~~~~~~~~
.. 
.. Wrapped dicts and lists can be modified and iterated just like native dicts
.. and lists::
.. 
..     >>> for key in wrapped:
..     ...     print(key, wrapped[key])
..     ...
..     ('motto', 'I gotta believe!')
..     ('activity', 'rapper')
.. 
.. Commits and Dirt
.. ~~~~~~~~~~~~~~~~
.. 
.. Until you call :func:`Object.commit`, any changes you've made to a wrapped
.. object will not be saved in the repository.  You can avoid the overhead of a
.. commit until you're ready.  Every wrapped object has a :attr:`Object.dirty`
.. property to let you know if it is out of sync with the repository::
.. 
..     >>> wrapped['licensed'] = True
..     >>> wrapped.dirty
..     True
..     >>> repo.get('parappa').value
..     {'motto': 'I gotta believe!', 'activity': 'rapper'}
..     >>> wrapped.commit()
..     >>> wrapped.dirty
..     False
..     >>> repo.get('parappa').value
..     {'motto': 'I gotta believe!', 'licensed': True, 'activity': 'rapper'}
.. 
.. .. _intuitive merging:
.. 
.. Intuitive Merging
.. ~~~~~~~~~~~~~~~~~
.. 
.. .. Wrapped objects make it easier to fork, edit, and merge keys::
.. 
..     

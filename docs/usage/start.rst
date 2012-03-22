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
    Object(key=foo,value='my very special bar',dirty=False)

You can commit any python object that will run through :func:`json.dumps`.
Numbers, booleans, strings, none, dicts, and lists are all OK::

    >>> repo.commit('number', 7)
    Object(key=number,value=7,dirty=False)
    >>> repo.commit('list', ['foo', 'bar'])
    Object(key=list,value=['foo', 'bar'],dirty=False)
    >>> repo.commit('dict', {'roses': 'red'})
    Object(key=dict,value={'roses', 'red'},dirty=False)

Each commit returns a reference to an :class:`Object` with the data that was
just committed to the repository.

Retrieving Data
~~~~~~~~~~~~~~~

Pulling the data back out is just a matter of retrieving the key::

    >>> foo = repo.get('foo')
    >>> foo
    Object(key=foo,value='my very special bar',dirty=False)
    >>> foo.value
    'my very special bar'

The returned object is wrapped in an :class:`Object`. The original value
is contained in the :attr:`Object.value` attribute, which preserves the
original type::

    >>> repo.get('list').value
    ['foo', 'bar']
    >>> type(repo.get('list').value)
    <type 'list'>
    >>> repo.get('dict').value
    {'roses': 'red'}
    >>> type(repo.get('dict').value)
    <type 'dict'>

Merging Data
~~~~~~~~~~~~

Keys can be merged back together if they split from a single commit.  First,
fork an existing key::

    >>> forked = repo.fork('forked', 'dict')
    >>> forked.value
    {'roses': 'red'}

Since `forked` and `dict` share some history, they can be merged later on.
Merging returns a :class:`Merge` with information about what happened::

    >>> repo.commit('dict', {'roses':'red', 'violets': 'blue'}
    >>> merge = repo.merge('forked', 'dict')
    >>> merge.message
    u'Auto-merge from a0a6a9acf82396365677ed8bdad12b766daaa72c'
    >>> repo.get('forked').value
    {'roses': 'red', 'violets': 'blue'}

Intervening changes to the `dict` object have been applied to `forked`.
Take a look at wrapped objects for an :ref:`intuitive <intuitive merging>` interface
for modification and merging.

Logs
~~~~

All the modifications to a key are available in its log::

    >>> repo.commit('president', 'washington')
    Object(key=president,value='washington',dirty=False)
    >>> repo.commit('president', 'adams')
    Object(key=president,value='adams',dirty=False)
    >>> repo.commit('president', 'madison')
    Object(key=president,value='madison',dirty=False)
    >>> log = repo.log('president')
    >>> for commit in log:
    ...     print(commit.object.value)
    ...
    madison
    adams
    washington

The :func:`Repository.log` method returns a generator that yields successively
deeper commits.  Each commit has a :attr:`Commit.object` property that gives
you access to the value at that point.

History
~~~~~~~

By default, :func:`Repository.get` returns the most recent commit for a key.
You can choose to pull something from further back on demand::

    >>> repo.get('president', back=2).value
    'washington'

Going too far back in time will raise a friendly reminder::

    >>> repo.get('president', back=300)
    IndexError: president has fewer than 300 commits

Wrapped Object Interface
------------------------

While all JsonGit actions can be mapped to methods on the :class:`Repository`,
it is often more convenient to keep a reference to a specific key, and call
methods upon it instead.

Wrapped objects let you do just that::

    >>> wrapped = repo.commit('parappa', {'activity': 'rapper'})
    >>> wrapped.key
    'parappa'
    >>> wrapped.value
    {'activity': 'rapper'}
    >>> wrapped['motto'] = 'I gotta believe!'
    >>> wrapped.commit()
    >>> repo.get('parappa').value
    {'motto': 'I gotta believe!', 'activity': 'rapper'}

Iteration
~~~~~~~~~

Wrapped dicts and lists can be modified and iterated just like native dicts
and lists::

    >>> for key in wrapped:
    ...     print(key, wrapped[key])
    ...
    ('motto', 'I gotta believe!')
    ('activity', 'rapper')

Commits and Dirt
~~~~~~~~~~~~~~~~

Until you call :func:`Object.commit`, any changes you've made to a wrapped
object will not be saved in the repository.  You can avoid the overhead of a
commit until you're ready.  Every wrapped object has a :attr:`Object.dirty`
property to let you know if it is out of sync with the repository::

    >>> wrapped['licensed'] = True
    >>> wrapped.dirty
    True
    >>> repo.get('parappa').value
    {'motto': 'I gotta believe!', 'activity': 'rapper'}
    >>> wrapped.commit()
    >>> wrapped.dirty
    False
    >>> repo.get('parappa').value
    {'motto': 'I gotta believe!', 'licensed': True, 'activity': 'rapper'}

.. _intuitive merging:

Intuitive Merging
~~~~~~~~~~~~~~~~~

.. Wrapped objects make it easier to fork, edit, and merge keys::

    

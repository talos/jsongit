.. _api:

API
===

This documentation covers JsonGit's interfaces.

Repos & Objects
~~~~~~~~~~~~~~~

JsonGit should be used through the public methods of :class:`models.Repository`
and :class:`models.Object`.  You should never need to use any class
constructors, instead using :func:`repo` to obtain your
:class:`models.Repository`.

The :class:`models.Object` wraps a key stored in its Repository.  You can
choose to ignore it and use the Repository as a key-value store.

.. module:: jsongit
.. autofunction:: repo

----------------------

.. module:: jsongit.models
.. autoclass:: Repository
   :inherited-members:
.. autoclass:: Object
   :inherited-members:

Diffs & Merges
~~~~~~~~~~~~~~

Repositories and objects provide an interface for merging.  These classes
provide methods to investigate merges.

.. autoclass:: Diff
   :inherited-members:
.. autoclass:: Conflict
   :inherited-members:

Exceptions
~~~~~~~~~~

.. module:: jsongit
.. autoexception:: NoGlobalSettingError
.. autoexception:: DifferentRepoError
.. autoexception:: BadKeyTypeError
.. autoexception:: NotJsonError

Utilities
~~~~~~~~~

These are convenience methods used internally by JsonGit.  They provide some
useful abstractions for :mod:`pygit2`.

.. module:: jsongit.utils
.. autofunction:: signature
.. autofunction:: global_config

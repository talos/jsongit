.. _api:

API
===

.. module:: jsongit

This documentation covers JsonGit's interfaces.

Repository
----------

JsonGit should be used through the public methods of :class:`Repository
<models.Repository>`.  You should use :func:`init` to obtain the object, not the constructor.

.. autofunction:: init

----------------------

.. module:: jsongit.models
.. autoclass:: Repository
   :inherited-members:

.. module:: jsongit.wrappers

Commit
------

.. autoclass:: Commit
   :inherited-members:

Diffs & Merges
--------------

The repository provides an interface for merging.  These classes provide
methods and properties to investigate merges.

.. autoclass:: Diff
   :inherited-members:
.. autoclass:: Conflict
   :inherited-members:

Exceptions
----------

.. module:: jsongit
.. autoexception:: NoGlobalSettingError
.. autoexception:: DifferentRepoError
.. autoexception:: InvalidKeyError
.. autoexception:: NotJsonError
.. autoexception:: StagedDataError

Utilities
---------

These are convenience methods used internally by JsonGit.  They provide some
useful abstractions for :mod:`pygit2`.

.. module:: jsongit.utils
.. autofunction:: signature
.. autofunction:: global_config

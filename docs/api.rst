.. _api:

API
===

.. module:: jsongit

This documentation covers the parts of JsonGit you should be using.

Repository
----------

.. autoclass:: JsonGitRepository
   :inherited-members:

Object
------

You can use JSONGit without ever touching the objects.  They are provided as a
convenience to access methods in their :class:`<JsonGitRepository>
JsonGitRepository`.  You should not instantiate them directly.

.. autoclass:: JsonGitObject
   :inherited-members:


Diff
----

Diffs are generated for you by JsonGit, you should not need to instantiate
them.

.. autoclass:: JsonDiff
   :inherited-members:

Exceptions
----------

.. autoexception:: NoGlobalSettingError
.. autoexception:: DifferentRepoError
.. autoexception:: BadKeyTypeError
.. autoexception:: NotJsonError

Other
-----

These are convenience methods used internally by JsonGit, but which you may
find useful.

.. autofunction:: signature
.. autofunction:: global_config

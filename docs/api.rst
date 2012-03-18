.. _api:

API
===

This documentation covers the parts of JsonGit you should be using.

Classes
----------

.. module:: jsongit.repository
.. autoclass:: JsonGitRepository
   :inherited-members:

.. module:: jsongit.object
.. autoclass:: JsonGitObject
   :inherited-members:

.. module:: jsongit.diff
.. autoclass:: JsonDiff
   :inherited-members:

Exceptions
----------

.. module:: jsongit
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

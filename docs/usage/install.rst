.. _install:

Installation
============

Installing JsonGit is easy.  It's recommended you install within a virtualenv_.

.. _virtualenv: http://www.virtualenv.org/en/latest/index.html

JsonGit has been tested with Python 2.7.

libgit2
-------

Libgit2_ is used to build and modify the git repository. You can find
instructions for installing it here_.

.. _Libgit2: http://libgit2.github.com/
.. _here: http://libgit2.github.com/#install

With Pip
--------

If you want to use JsonGit in your project now, pip_ is the fastest and easiest
way to install.

.. _pip: http://www.pip-installer.org/

JsonGit is hosted on PyPI_, so you can install it in one line::

    $ pip install jsongit

.. _PyPI: http://pypi.python.org/pypi

From Source
-----------

If you want to hack on JsonGit, you should grab the source.

You can clone it from the `GitHub respository`_::

    $ git clone https://github.com/talos/jsongit.git

.. _GitHub repository: https://github.com/talos/jsongit

Then, install the requirements::

    $ cd jsongit
    $ pip install -r requirements.txt

Finally, install jsongit::

    $ python setup.py install

Testing
~~~~~~~

If you've installed from source, it's easy to make sure everything works.

::

    $ pip install nose
    $ nosetests

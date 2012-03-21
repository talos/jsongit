Installation
============

Libraries
~~~~~~~~~

You'll need `libgit2 <http://libgit2.github.com/>`_, whose installation
instructions can be found `here <http://libgit2.github.com/#install>`_.

Modules
~~~~~~~

All Python module depenedencies are on PyPI, so all you need to do
(preferably in a virtualenv):

::

  % git clone https://github.com/talos/jsongit.git
  % cd jsongit
  % pip install -r requirements.txt
  % python setup.py install

Testing
~~~~~~~

It's easy to make sure everything works.

::

  % pip install nose
  % nosetests

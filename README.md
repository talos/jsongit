# GitDict

*git for your dict*

## Installation

GitDict requires [pygit2][] and [json_diff][].  Pygit2 depends upon libgit2, 
which has its own set of dependencies.  Information on installing libgit2 can 
be found [here][].

  [pygit2]: https://github.com/libgit2/pygit2 
  [json_diff]: https://fedorahosted.org/json_diff/
  [here]: http://libgit2.github.com/

```python
pip install pygit2
pip install json_diff
git clone https://github.com/talos/gitdict.git
cd gitdict
python setup.py install
```

Make sure it works:

```python
pip install nose
nosetests
```

## Documentation 

Documentation is on [Read the Docs][].

  [Read the Docs]: http://gitdict.readthedocs.org

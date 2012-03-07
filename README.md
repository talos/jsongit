# DictGit

### Git for your dict

===

### Installation

DictGit requires pygit2 and json_diff.  Pygit2 depends upon libgit2, which
has its own set of dependencies.  Information on installing libgit2 can be
found [here](http://libgit2.github.com/).

```python
pip install pygit2
pip install json_diff
```

The tests run using nose.

```python
pip install nose
nosetests test/dictgit.py
```

### API

Better documentation is coming.  For now, take a look at the tests file.

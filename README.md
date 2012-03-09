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

## Example

```python
>>> from gitdict import DictRepository, DictAuthor
>>> repo = DictRepository('tmp', author=DictAuthor('me', 'me@me.com'))
>>> foo = repo.create('foo', {'roses': 'red'})
>>> bar = repo.clone(foo, 'bar')
>>> bar = repo.create('bar', {'roses': 'red'})
>>> foo['violets'] = 'blue'
>>> foo
GitDict({u'roses': u'red', 'violets': 'blue'})
>>> foo.dirty
True
>>> foo.commit()
>>> foo.dirty
False
>>> foo
GitDict({u'roses': u'red', 'violets': 'blue'})
>>> bar
GitDict({u'roses': u'red'})
>>> bar.merge(foo)
True
>>> bar
GitDict({u'roses': u'red', u'violets': u'blue'})
```

## Documentation 

Documentation is on [Read the Docs][].

  [Read the Docs]: http://gitdict.readthedocs.org

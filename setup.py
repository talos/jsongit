#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    # Install prereqs here and now if we can.
    from setuptools import setup
    kw = { 'install_requires': [
        'pygit2>=0.16.1',
        'json_diff>=1.2.9'
    ] }
except ImportError:
    from distutils.core import setup
    print 'No setuptools.  Do\n\n    $ pip install pygit2\n    $ pip install json_diff\n\nto install dependencies.'
    kw = {}

execfile('jsongit/version.py')

packages = ['jsongit']

setup(
    name='jsongit',
    version=__version__,
    description='Git for JSON',
    long_description=open('README.rst').read(),
    author='John Krauss',
    author_email='john@accursedware.com',
    url='http://github.com/talos/jsongit',
    packages=packages,
    license='BSD',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
    ),
    **kw
)

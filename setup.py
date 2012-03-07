#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dictgit

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

required = ['pygit2','json_diff']
packages = ['dictgit']

setup(
    name='dictgit',
    version=dictgit.__version__,
    description='Git for your Dict',
    long_description=open('README.md').read(),
    author='John Krauss',
    author_email='john@accursedware.com',
    url='http://github.com/talos/dictgit',
    packages=packages,
    install_requires=required,
    license='BSD',
    classifiers=(
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7'
    ),
)

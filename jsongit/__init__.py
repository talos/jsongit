# -*- coding: utf-8 -*-

__title__ = 'jsongit'
__version__ = '0.0.1'
__build__ = 0x000001
__author__ = 'John Krauss'
__license__ = 'BSD'
__copyright__ = 'Copyright 2012 John Krauss'

from .repository import JsonGitRepository
from .signature import signature, global_config
from .object import JsonGitObject
from .diff import JsonDiff

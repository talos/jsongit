# -*- coding: utf-8 -*-

__title__ = 'gitdict'
__version__ = '0.0.2'
__build__ = 0x000002
__author__ = 'John Krauss'
__license__ = 'BSD'
__copyright__ = 'Copyright 2012 John Krauss'

from .repository import DictRepository
from .author import DictAuthor
from .dict import GitDict
from .diff import DictDiff
from .exceptions import NoGlobalAuthor

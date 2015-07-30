#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""psutil is a module providing convenience functions for managing
processes and gather system information in a portable way by using
Python.

Available documentation :
	* linuxutil.pid
	* linuxutil.net"""

#from linuxutil._common import *
import linuxutil.net, linuxutil.pid, linuxutil.disk

__version__ = '0.1.1'
__author__ = 'G. LE MEUR'
__date__ = '24/04/2012'

version_info = tuple([int(_x) for _x in __version__.split('.')])
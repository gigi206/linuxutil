#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re
from linuxutil._common import *

# See http://wiki.osdev.org/PCI

if os.path.isfile('/usr/share/misc/pci.ids'):
	filePci = '/usr/share/misc/pci.ids'
else:
	filePci = os.path.join(os.path.dirname(__file__), 'pci.ids')

#@wrapException
def pciname(vendor, device = '', subVendor = '', subDevice = ''):
	_find_vendor, _find_device, _find_subSystem = False, False, False
	
	for _x in open(filePci).readlines():
		if _find_vendor and not re.match('^\t', _x):
			return [vendor, device, '%s  %s' % (subVendor, subDevice)]
			
		if re.match('^%s\s' % vendor[2:], _x):
			_find_vendor = True
			vendor = ' '.join(_x.split()[1:])
			
		if _find_vendor and re.match('^\t%s\s' % device[2:], _x):
			_find_device = True
			device = ' '.join(_x.split()[1:])
			
		if _find_device and re.match('^\t\t%s\s%s\s' % (subVendor[2:], subDevice[2:]), _x):
			_find_subSystem = True
			subSystem = ' '.join(_x.split()[2:])
			return [vendor, device, subSystem]
		
	#If end of file and not found
	return [vendor, device, '%s  %s' % (subVendor, subDevice)]

#@wrapException
def classname(classid):
	_findL1, _findL2, _findL3 = False, False, False
	_classNameL1, _classNameL2, _classNameL3 = '', '', ''
	
	for _x in open(filePci).readlines():
		if _findL1 and not re.match('^\t', _x):
			return [_classNameL1, _classNameL2, _classNameL3]
			
		if re.match('^C\s%s\s' % classid[2:4], _x):
			_findL1 = True
			_classNameL1 = ' '.join(_x.split()[2:])
			
		if _findL1 and re.match('^\t%s\s' % classid[4:6], _x):
			_findL2 = True
			_classNameL2 = ' '.join(_x.split()[1:])
			
		if _findL2 and re.match('^\t\t%s\s' % classid[6:8], _x):
			_findL3 = True
			_classNameL3 = ' '.join(_x.split()[1:])
			return [_classNameL1, _classNameL2, _classNameL3]
	
	#If end of file and not found
	return [classid]
	
#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os, sys, time

if os.uname()[0].lower() == 'linux':
	ProcessPath = '/proc'
else:
	raise OSError('%s not supported' % os.uname[0])
	sys.exit(1)

#if os.getuid() != 0:
	#raise OSError('This program needs to be run with root account !')
	#sys.exit(1)
	
#Decorator
def wrapException(f):
	def wrapped(*args, **kwargs):
		try:
			int(show_error)
		except:
			show_error = 1
		
		try:
			return f(*args, **kwargs)
		except:
			if show_error == 0:
				return False
			elif show_error == 1:
				return f(*args, **kwargs)
	
	wrapped.__doc__ = f.__doc__
	wrapped.__name__ = f.__name__
	return wrapped

#Decorator
def timeIt(f):
	def timed(*args, **kw):
		ts = time.time()
		result = f(*args, **kw)
		te = time.time()
		print('%r (%r, %r) %f sec' % (f.__name__, args, kw, te-ts))
		return result
	return timed
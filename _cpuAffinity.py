#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Has been modified by me to be compatible with python3.
Source : http://nullege.com/codes/show/src@a@f@affinity-HEAD@affinity@__init__.py

Copyright (c) 2009 Henrik Gustafsson <henrik.gustafsson@fnord.se>
  
Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.
  
THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
'''
  
try:
	import ctypes, ctypes.util
	import os

	_ncpus = os.sysconf('SC_NPROCESSORS_ONLN')

	if _ncpus < 1:
		raise ImportError('Unsupported platform')

	_libc = ctypes.CDLL(ctypes.util.find_library('c'))

	_NCPUBITS = ctypes.sizeof(ctypes.c_ulong)
	_CPU_SET_SIZE = 1024

	class _cpuset(ctypes.Structure):
		_fields_ = [("bits", ctypes.c_ulong * (int(_CPU_SET_SIZE / _NCPUBITS)))]
		
		def __init__(self, l = None):
			for x in range(int(_CPU_SET_SIZE / _NCPUBITS)):
				self.bits[x] = 0
			if l:
				for c in l:
					self.enable(c)
		
		def enable(self, n):
			if n < 0 or n >= _ncpus:
				raise ValueError('CPU id out of bounds')
			self.bits[int(n / _NCPUBITS)] |= 1 << (n % _NCPUBITS)
	
		def is_enabled(self, n):
			if n < 0 or n >= _ncpus:
				raise ValueError('CPU id out of bounds')
			return ((self.bits[int(n / _NCPUBITS)]) & (1 << (n % _NCPUBITS))) != 0
		
		def to_list(self):
			return [ i for i in range(_ncpus) if self.is_enabled(i) ]



	_sched_setaffinity = _libc.sched_setaffinity
	_sched_setaffinity.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(_cpuset)]
	_sched_setaffinity.restype = ctypes.c_int

	_sched_getaffinity = _libc.sched_getaffinity
	_sched_getaffinity.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(_cpuset)]
	_sched_getaffinity.restype = ctypes.c_int

	_errno_location = _libc.__errno_location
	_errno_location.restype = ctypes.POINTER(ctypes.c_int)

	def _get_errno():
		return _errno_location().contents.value

	def set_cpu_affinity(cpus, pid = 0):
		mask = _cpuset(cpus)
		result = _sched_setaffinity(pid, ctypes.sizeof(_cpuset), mask)
		#if result != 0:
		#    e = _get_errno()
		#    raise OSError(e, os.strerror(e))

		if result != 0:
			return False
		else:
			return True

	def get_cpu_affinity(pid = 0):
		mask = _cpuset()
		result = _sched_getaffinity(pid, ctypes.sizeof(_cpuset), mask)
		if result != 0:
			e = _get_errno()
			raise OSError(e, os.strerror(e))
		return mask.to_list()

except(OSError, AttributeError):
	raise ImportError('Unsupported platform')

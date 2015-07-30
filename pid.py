#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, time
from linuxutil._common import *
import linuxutil._cpuAffinity

#@wrapException
def ls(): 
	"""
	Desc : list pid of running process
	Args : None
	Ret  : List of Int
	"""
	return [int(_x) for _x in os.listdir(ProcessPath) if _x.isdigit()]

#@wrapException
def renice(who, prio = 0, which = 0):
	"""
	Desc : Alter cpu priority of running processes, group processes or user processes. Default priority is 0 and is a PRIO_PROCESS (0)
	Args :	* who (int) : Is defined according to which value : a pid is wich == 0, a group id if which == 1 or a user if which == 2
		* which (int) : Must be a value between 0 and 2 (PRIO_PROCESS = 0, PRIO_PGRP = 1, ou PRIO_USER = 2). (0 by default : PRIO_PROCESS)
		* prio (int) : Priority between -20 and 19 (0 by default)
	Ret  : Bool
	"""
	import ctypes, ctypes.util

	#who = ctypes.c_int(who).value
	#prio = ctypes.c_int(prio).value
	#which = ctypes.c_int(which).value
	
	int(who)
	int(prio)
	int(which)
	
	libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
	_ret = libc.setpriority(which, who, prio)
	
	if _ret == 0:
		return True
	else:
		return False

class id:
	"""
	Desc : Represents an OS process
	Type : Class
	Ret  : Object
	"""

	def __init__(self, pid):
		"""
		Desc : Create a new Process object, raises OSError if the PID does not exist, and ValueError if the parameter is not an integer PID
		Args : pid (int)
		Ret  : Objet
		"""

		self.pid = int(pid)

		#if self.pid == '':
			#self.pid = os.getpid()
		
		self._ProcPidPath = os.path.join(ProcessPath, str(self.pid))

		#if not isinstance(self.pid, int):
			#raise ValueError("An integer is required")

		if not self.isrunning:
			raise OSError("No such process found with pid %d" % self.pid)

	@property
	#@wrapException
	def exe(self):
		"""
		Desc : Absolute path name
		Args : None
		Ret  : String
		"""
		return os.readlink(os.path.join(self._ProcPidPath, 'exe'))

	@property
	#@wrapException
	def cwd(self):
		"""
		Desc : Current working directory
		Args : None
		Ret  : String
		"""
		return os.readlink(os.path.join(self._ProcPidPath, 'cwd'))

	@property
	#@wrapException
	def root(self):
		"""
		Desc : The root fylesystem view by the process
		Args : None
		Ret  : String
		"""
		return os.readlink(os.path.join(self._ProcPidPath, 'root'))

	@property
	#@wrapException
	def cmdline(self):
		"""
		Desc : The process command line
		Args : None
		Ret  : List
		"""
		return open(os.path.join(self._ProcPidPath, 'cmdline'), 'r').read().split('\x00')

	@property
	#@wrapException
	def environ(self):
		"""
		Desc : List of the process environment
		Args : None
		Ret  : List
		"""
		return open(os.path.join(self._ProcPidPath, 'environ'), 'r').read().split('\x00')

	@property
	#@wrapException
	def name(self):
		"""
		Desc : Process name
		Args : None
		Ret  : String
		"""
		return open(os.path.join(self._ProcPidPath, 'comm'), 'r').read().rstrip('\n')

	@property
	#@wrapException
	def io(self):
		"""
		Desc : io counters
		Args : None
		Ret  : Dict 
			* write_bytes : write bytes
			* read_bytes : read bytes
			* cancelled_write_bytes : cancelled write bytes
			* syscw : write counters for number of I/O operation. We may use then to compute average amount of data passed in one system call.
			* syscr : read counters for number of I/O operation. We may use then to compute average amount of data passed in one system call.
			* wchar : write characters
			* rchar : read characters
		"""
		_x = dict([_x.replace(':','').split() for _x in open(os.path.join(self._ProcPidPath, 'io'), 'r').readlines()])

		for _k,_v in _x.items(): 
			_x[_k] = int(_v)
		return _x

	@property
	#@wrapException
	def memfiles(self):
		"""
		Desc : mapped memory files
		Args : None
		Ret  : List
		"""
		return list(set([_x.split()[-1] for _x in open(os.path.join(self._ProcPidPath, 'maps'), 'r').readlines() if _x.split()[-1][0]=='/']))

	@property
	#@wrapException
	def status(self):
		"""
		Desc : Various information about process
		Args : None
		Ret  : Dict containing List
		"""
		_x={}
		for _i in [_i.replace(':', '').split() for _i in open(os.path.join(self._ProcPidPath, 'status'), 'r').readlines()]:
			_x[_i[0]] = _i[1:]
		return _x

	@property
	#@wrapException
	def tid(self):
		"""
		Desc : First thread pid (Thread group ID)
		Args : None
		Ret  : Int
		"""
		return int(self.status['Tgid'][0])

	@property
	#@wrapException
	def tracerpid(self):
		"""
		Desc : PID of process tracing this process (0 if not being traced)
		Args : None
		Ret  : Int
		"""
		return int(self.status['TracerPid'][0])

	@property
	#@wrapException
	def uid(self):
		"""Desc : uids of a process
		Args : None
		Ret  : Dict
			-> real
			-> effective
			-> saved
			-> filesystem
		"""
		_real, _effective, _saved, _filesystem =  self.status['Uid']
		return {'real': int(_real), 'effective': int(_effective), 'saved': int(_saved), 'filesystem': int(_filesystem)}

	@property
	#@wrapException
	def gid(self):
		"""Desc : gids of a process
		Args : None
		Ret  : Dict
			-> real
			-> effective
			-> saved
			-> filesystem
		"""
		_real, _effective, _saved, _filesystem =  self.status['Gid']
		return {'real': int(_real), 'effective': int(_effective), 'saved': int(_saved), 'filesystem': int(_filesystem)}

	@property
	#@wrapException
	def fdsize(self):
		"""
		Desc : Number of file descriptor slots currently allocated
		Args : None
		Ret  : Int
		"""
		return int(self.status['FDSize'][0])

	@property
	#@wrapException
	def vmpeak(self):
		"""
		Desc : Peak virtual memory size
		Args : None
		Ret  : Dict
		"""
		_value, _unit = self.status['VmPeak']
		return {'value': int(_value), 'unit': _unit}

	@property
	#@wrapException
	def vmsize(self):
		"""
		Desc : Virtual memory size
		Args : None
		Ret  : Dict
		"""
		_value, _unit = self.status['VmSize']
		return {'value': int(_value), 'unit': _unit}

	@property
	#@wrapException
	def vmlck(self):
		"""
		Desc : Locked memory size
		Args : None
		Ret  : Dict
		"""
		_value, _unit = self.status['VmLck']
		return {'value': int(_value), 'unit': _unit}

	@property
	#@wrapException
	def vmhwm(self):
		"""
		 Desc : Peak resident set size
		Args : None
		Ret  : Dict
		"""
		_value, _unit = self.status['VmHWM']
		return {'value': int(_value), 'unit': _unit}

	@property
	#@wrapException
	def vmrss(self):
		"""
		Desc : Resident set size
		Args : None
		Ret  : Dict
		"""
		_value, _unit = self.status['VmRSS']
		return {'value': int(_value), 'unit': _unit}

	@property
	#@wrapException
	def vmdata(self):
		"""
		Desc : VmStk, VmExe: Size of data, stack, and text segments
		Args : None
		Ret  : Dict
		"""
		_value, _unit = self.status['VmData']
		return {'value': int(_value), 'unit': _unit}

	@property
	#@wrapException
	def vmlib(self):
		"""
		Desc : Shared library code size
		Args : None
		Ret  : Dict
		"""
		_value, _unit = self.status['VmLib']
		return {'value': int(_value), 'unit': _unit}

	@property
	#@wrapException
	def vmpte(self):
		"""
		Desc : Page table entries size
		Args : None
		Ret  : Dict
		"""
		_value, _unit =  self.status['VmPTE']
		return {'value': int(_value), 'unit': _unit}

	@property
	#@wrapException
	def state(self):
		"""
		Desc : Current state of the process.  One of "R (running)", "S (sleeping)", "D (disk sleep)", "T (stopped)", "T (tracing stop)", "Z (zombie)", or "X (dead)"
		Args : None
		Ret  : Dict
			short : one letter description
			long : one word description
		"""
		_short, _long = self.status['State']
		return {'short': _short, 'long': _long[1:-1]}

	@property
	#@wrapException
	def ppid(self):
		"""
		Desc : PID of parent process
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[3])

	@property
	#@wrapException
	def pgrp(self):
		"""
		Desc : The process group ID of the process
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[4])

	@property
	#@wrapException
	def session(self):
		"""
		Desc : The session ID of the process
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[5])

	@property
	#@wrapException
	def ttynr(self):
		"""
		Desc : The controlling terminal of the process. (The minor device number is contained in the combination of bits 31 to 20 and 7 to 0; the major device number is in bits 15 to 8.)
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[6])

	@property
	#@wrapException
	def tpgid(self):
		"""
		Desc : The ID of the foreground process group of the controlling terminal of the process
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[7])

	@property
	#@wrapException
	def flags(self):
		"""The kernel flags word of the process."""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[8])

	@property
	#@wrapException
	def minflt(self):
		"""
		Desc : The number of minor faults the process has made which have not required loading a memory page from disk
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[9])

	@property
	#@wrapException
	def cminflt(self):
		"""
		Desc : The number of minor faults that the process's waited-for children have made
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[10])

	@property
	#@wrapException
	def majflt(self):
		"""
		Desc : The number of major faults the process has made which have required loading a memory page from disk
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[11])

	@property
	#@wrapException
	def cmajflt(self):
		"""
		Desc : The number of major faults that the process's waited-for children have made
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[12])

	@property
	#@wrapException
	def utime(self):
		"""
		Desc : Amount of time that this process has been scheduled in user mode, measured in clock ticks
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[13])

	@property
	#@wrapException
	def stime(self):
		"""
		Desc : Amount of time that this process has been scheduled in kernel mode, measured in clock ticks
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[14])

	@property
	#@wrapException
	def cutime(self):
		"""
		Desc : Amount of time that this process's waited-for children have been scheduled in user mode, measured in clock ticks
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[15])

	@property
	#@wrapException
	def cstime(self):
		"""
		Desc : Amount of time that this process's waited-for children have been scheduled in kernel mode, measured in clock ticks
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[16])

	@property
	#@wrapException
	def priority(self):
		"""The kernel stores nice values as numbers in the range 0 (high) to 39 (low), corresponding to the user-visible nice range of -20 to 19."""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[17])

	@property
	#@wrapException
	def nice(self):
		"""
		Desc : Nice value : a value in the range 19 (low priority) to -20 (high priority)
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[18])

	@property
	#@wrapException
	def numthreads(self):
		"""
		Desc : Number of threads in this process
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[19])

	@property
	#@wrapException
	def itrealvalue(self):
		"""
		Desc : The time in jiffies before the next SIGALRM is sent to the process due to an interval timer
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[20])

	@property
	#@wrapException
	def starttime(self):
		"""
		Desc : The time in jiffies the process started after system boot
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[21])

	@property
	#@wrapException
	def vsize(self):
		"""
		Desc : Virtual memory size in bytes
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[21])

	@property
	#@wrapException
	def rss(self):
		"""
		Desc : Resident Set Size: number of pages the process has in real memory.  This is just the pages which count toward text, data, or stack space.  This does not include pages which have not been demand-loaded in, or which are swapped out
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[23])

	@property
	#@wrapException
	def rsslim(self):
		"""
		Desc : Current soft limit in bytes on the rss of the process
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[24])

	@property
	#@wrapException
	def startcode(self):
		"""
		Desc : The address above which program text can run
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[25])

	@property
	#@wrapException
	def endcode(self):
		"""
		Desc : The address below which program text can run
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[26])

	@property
	#@wrapException
	def startstack(self):
		"""
		Desc : The current value of ESP (stack pointer), as found in the kernel stack page for the process
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[27])

	@property
	#@wrapException
	def kstkesp(self):
		"""
		Desc : The current value of ESP (stack pointer), as found in the kernel stack page for the process
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[28])

	@property
	#@wrapException
	def kstkeip(self):
		"""
		Desc : The current EIP (instruction pointer)
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[29])

	@property
	#@wrapException
	def wchan(self):
		"""
		Desc : This is the "channel" in which the process is waiting. It is the address of a system call, and can be looked up in a namelist if you need a textual name
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[34])

	@property
	#@wrapException
	def exitsignal(self):
		"""
		Desc : Signal to be sent to parent when we die
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[37])

	@property
	#@wrapException
	def processor(self):
		"""
		Desc : CPU number last executed on
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[38])

	@property
	#@wrapException
	def rt_priority(self):
		"""
		Desc : Real-time scheduling priority, a number in the range 1 to 99 for processes scheduled under a real-time policy, or 0, for non-real-time processes (see sched_setscheduler(2))
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[39])

	@property
	#@wrapException
	def policy(self):
		"""
		Desc : Scheduling policy (see sched_setscheduler(2))
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[40])

	@property
	#@wrapException
	def delayacct_blkio_ticks(self):
		"""
		Desc : Aggregated block I/O delays, measured in clock ticks (centiseconds)
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[41])

	@property
	#@wrapException
	def guest_time(self):
		"""
		Desc : Guest time of the process (time spent running a virtual CPU for a guest operating system), measured in clock ticks
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[42])

	@property
	#@wrapException
	def cguest_time(self):
		"""
		Desc : Guest time of the process's children, measured in clock ticks
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self._ProcPidPath, 'stat'), 'r').read().split()[43])

	#@wrapException
	def signal(self, signal = 15):
		"""
		Desc : Send signal to the process
		Args (Int ou String) : default is 15 (SIGTERM)

		1) SIGHUP       2) SIGINT       3) SIGQUIT      4) SIGILL
		5) SIGTRAP      6) SIGABRT      7) SIGBUS       8) SIGFPE
		9) SIGKILL     10) SIGUSR1     11) SIGSEGV     12) SIGUSR2
		13) SIGPIPE     14) SIGALRM     15) SIGTERM     16) SIGSTKFLT
		17) SIGCHLD     18) SIGCONT     19) SIGSTOP     20) SIGTSTP
		21) SIGTTIN     22) SIGTTOU     23) SIGURG      24) SIGXCPU
		25) SIGXFSZ     26) SIGVTALRM   27) SIGPROF     28) SIGWINCH
		29) SIGIO       30) SIGPWR      31) SIGSYS      34) SIGRTMIN
		35) SIGRTMIN+1  36) SIGRTMIN+2  37) SIGRTMIN+3  38) SIGRTMIN+4
		39) SIGRTMIN+5  40) SIGRTMIN+6  41) SIGRTMIN+7  42) SIGRTMIN+8
		43) SIGRTMIN+9  44) SIGRTMIN+10 45) SIGRTMIN+11 46) SIGRTMIN+12
		47) SIGRTMIN+13 48) SIGRTMIN+14 49) SIGRTMIN+15 50) SIGRTMAX-14
		51) SIGRTMAX-13 52) SIGRTMAX-12 53) SIGRTMAX-11 54) SIGRTMAX-10
		55) SIGRTMAX-9  56) SIGRTMAX-8  57) SIGRTMAX-7  58) SIGRTMAX-6
		59) SIGRTMAX-5  60) SIGRTMAX-4  61) SIGRTMAX-3  62) SIGRTMAX-2
		63) SIGRTMAX-1  64) SIGRTMAX

		Ret  : Bool
		"""
		_signal = {
			'SIGHUP' : 1,
			'SIGINT' : 2,
			'SIGQUIT' : 3,
			'SIGILL' : 4,
			'SIGTRAP' : 5,
			'SIGABRT' : 6,
			'SIGBUS' : 7,
			'SIGFPE' : 8,
			'SIGKILL' : 9,
			'SIGUSR1' : 10,
			'SIGSEGV' : 11,
			'SIGUSR2' : 12,
			'SIGPIPE' : 13,
			'SIGALRM' : 14,
			'SIGTERM' : 15,
			'SIGSTKFLT' : 16,
			'SIGCHLD' : 17,
			'SIGCONT' : 18,
			'SIGSTOP' : 19,
			'SIGTSTP' : 20,
			'SIGTTIN' : 21,
			'SIGTTOU' : 22,
			'SIGURG' : 23,
			'SIGXCPU' : 24,
			'SIGXFSZ' : 25,
			'SIGVTALRM' : 26,
			'SIGPROF' : 27,
			'SIGWINCH' : 28,
			'SIGIO' : 29,
			'SIGPWR' : 30,
			'SIGSYS' : 31,
			'SIGRTMIN' : 34,
			'SIGRTMIN+1' : 35,
			'SIGRTMIN+2' : 36,
			'SIGRTMIN+3' : 37,
			'SIGRTMIN+4' : 38,
			'SIGRTMIN+5' : 39,
			'SIGRTMIN+6' : 40,
			'SIGRTMIN+7' : 41,
			'SIGRTMIN+8' : 42,
			'SIGRTMIN+9' : 43,
			'SIGRTMIN+10' : 44,
			'SIGRTMIN+11' : 45,
			'SIGRTMIN+12' : 46,
			'SIGRTMIN+13' : 47,
			'SIGRTMIN+14' : 48,
			'SIGRTMIN+15' : 49,
			'SIGRTMAX-14' : 50,
			'SIGRTMAX-13' : 51,
			'SIGRTMAX-12' : 52,
			'SIGRTMAX-11' : 53,
			'SIGRTMAX-10' : 54,
			'SIGRTMAX-9' : 55,
			'SIGRTMAX-8' : 56,
			'SIGRTMAX-7' : 57,
			'SIGRTMAX-6' : 58,
			'SIGRTMAX-5' : 59,
			'SIGRTMAX-4' : 60,
			'SIGRTMAX-3' : 61,
			'SIGRTMAX-2' : 62,
			'SIGRTMAX-1' : 63,
			'SIGRTMAX' : 64
		}

		if isinstance(signal, str):
			if signal in _signal:
				signal = _signal[signal]
			else:
				raise ValueError("%s is not a valid signal" % signal)

		os.kill(self.pid, int(signal))
		return True

	#@wrapException
	def renice(self, prio = 0):
		"""
		Desc : Change the cpu prority of the process between -20 to 19. Return True if success or False is not
		Args : Priority (int) beetween -20 and 19
		Ret  : Bool
		"""
		return renice(self.pid, prio, 0)

	#@wrapException
	def iorenice(self, ioclass = 0, iolevel = 0):
		"""
		Desc : Alter io priority of running processes. Default priority is None
		Args : 	* iolevel (int) : scheduling class data -> 0-7 for realtime and best-effort classes
			* ioclass (int) : scheduling class name or number -> 0: none, 1: realtime, 2: best-effort, 3: idle
		Ret  : Bool
		Warn : Only CFQ scheduler is compatible with io priority, see what is your is scheduler in /sys/block/<disk>/queue/scheduler
		Arch : i386, x86_64, ppc, ia64
		"""

		import ctypes, ctypes.util
		libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
		_score = ioclass * 8192 + iolevel
		_myarch = os.uname()[-1].lower()

		#See id syscall in /usr/src/`uname -r`/Documentation/block/ioprio.txt
		_syscallId = {
			'i386': 289,
			'i586': 289,
			'i686': 289,
			'x86_64': 251,
			'ppc': 273,
			'ia64': 1274
		}
		
		if _myarch not in _syscallId:
			raise OSError("Architecture %s is not yet supported" % _myarch)
		
		_ret = libc.syscall(_syscallId[_myarch], 1, self.pid, _score, 0)

		if _ret == 0:
			return True
		else:
			return False

	@property
	#@wrapException
	def ionice(self):
		"""
		Desc : Alter io priority of running processes. Default priority is None
		Args : None
		Ret  :	* id dor the priority. Exemple io priority with class 2 and level 5 have an id of 16389
			* class (int) : scheduling class name or number -> 0: none, 1: realtime, 2: best-effort, 3: idle
			* level (int) : scheduling class data -> 0-7 for realtime and best-effort classes
		Arch : i386, x86_64, ppc, ia64.
		Warn : only CFQ scheduler is compatible with io priority, see what is your is scheduler in /sys/block/<disk>/queue/scheduler
		"""
		
		import ctypes, ctypes.util
		libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))

		#See id syscall in /usr/src/`uname -r`/Documentation/block/ioprio.txt
		_syscallId = {
			'i386': 290,
			'i586': 290,
			'i686': 290,
			'x86_64': 252,
			'ppc': 274,
			'ia64': 1275
		}

		_ret = libc.syscall(_syscallId[os.uname()[-1].lower()], 1, self.pid, self.pid, 0)

		if _ret == None or _ret == -1:
			return False
		else:
			return {'level': int(_ret % 8192), 'class': int(_ret / 8192), 'id': _ret}

	#@wrapException
	def wait(self, wtime = 0, sleep = 0.1):
		"""
		Desc : Wait the end of a process, or wait a process for a specific time. The step time is 0.1 by default
		Args :	* wtime : the time to wait for the process (default is 0 means infinite time)
			* sleep : the schecdule check to wait if the process is running (default is 0.1 means check if process is running all the 0.1sec)
		Ret  : Bool (True is the process has finish before the wtime, Fale if process is stiil running before the wtime)
		"""
		_x = time.time()

		while self.isrunning:
			time.sleep(sleep)
			_y = time.time() - _x
			if _y > wtime and wtime != 0:
				return False
		
		return True

	@property
	#@wrapException
	def tty(self):
		"""
		Desc : The name of the TTY
		Args : None
		Ret  : List of strings
		"""
		return set([ _x['name'] for _x in self.fd.values() if os.isatty(os.open(_x['name'], os.O_RDONLY)) and _x['name'].startswith('/')])
		
	@property
	#@wrapException
	def threadnotid(self):
		"""
		Desc : Threads list without the tid
		Args : None
		Ret  : List of Int
		"""
		return [int(_x) for _x in os.listdir(os.path.join(self._ProcPidPath, 'task')) if not re.match('^%d$' % self.tid, _x)]

	@property
	#@wrapException
	def thread(self):
		"""
		Desc : Threads list with the tid
		Args : None
		Ret : List of Int
		"""
		return [int(_x) for _x in os.listdir(os.path.join(self._ProcPidPath, 'task'))]

	@property
	#@wrapException
	def fd(self):
		"""
		Desc : List num of fd and informations about it
		Args : None
		Ret  : Dict of Int -> id {info: value}
		"""
		_y = {}

		for _fd in os.listdir(os.path.join(self._ProcPidPath, 'fd')):
			try: #For correct a bug (if os.listdir browse the current python fd directory, it will generate a new fd (just for os.readlink) and it will impossible to read the link because it will have disappeared !). Solution : just pass the ghost fd
				_x = os.readlink(os.path.join(self._ProcPidPath, 'fd', _fd))
			except:
				continue
			
			_y[int(_fd)] = {}
			
			try:
				_i = _x.index(':')
				_y[int(_fd)]['type'] = _x[0:_i]
				if _x[-1] == ']':
					_y[int(_fd)]['name'] = _x[_i+2:-1]
				else:
					_y[int(_fd)]['name'] = _x[_i+1:]
			except:
				_y[int(_fd)]['type'] = 'file'
				_y[int(_fd)]['name'] = _x

			for l in open(os.path.join(self._ProcPidPath, 'fdinfo', _fd)).readlines():
				_k, _v = l.split(':')
				_y[int(_fd)][_k] = int(_v.strip())
		return _y

	@property
	#@wrapException
	def isrunning(self):
		"""
		Desc : Does the pid exist ?
		Args : None
		Ret  : Bool
		"""
		return os.path.isdir(self._ProcPidPath)

	@property
	def isthread(self):
		"""
		Desc : Does the pid is a thread ?
		Args : None
		Ret  : bool
		"""
		if self.tid == self.pid:
			return False
		else:
			return True

	@property
	def parent(self):
		"""
		Desc : Object id of parent pid
		Args : None
		Ret  : Obj
		"""
		return id(self.ppid)

	@property
	#@wrapException
	def parents(self):
		"""
		Desc : Parents pid of the process tree
		Args : None
		Ret  : List of Int
		"""
		if not self.isrunning:
			return False

		_y = self.pid
		_x = []		

		while id(_y).pid != 1:
			_y = id(_y).ppid
			_x.append(_y)

		return _x

	@property
	#@wrapException
	def numparents(self):
		"""
		Desc : Number of parents of teh process
		Args : None
		Ret  : Int
		"""
		return len(self.parents)

	@property
	#@wrapException
	def cpid(self):
		"""
		Desc : List of children pid (cpid for children pid)
		Args : None
		Ret : List of Int
		"""
		return [_x for _x in ls() if id(_x).ppid == self.pid]

	@property
	#@wrapException
	def numchildren(self):
		"""
		Desc : The number of children pid (int)
		Args : None
		Ret  : Int
		"""
		return len(self.cpid)

	@property
	#@wrapException
	def children(self):
		"""
		Desc : List of id Objets
		Args : None
		Ret  : List of Objets
		"""
		return [pid(_x) for _x in ls() if pid(_x).ppid == self.pid]

	#@wrapException
	def setcpu(self, cpus):
		"""
		Desc : Set authorized cpu(s) 
		Args : cpus = List of processor id (int)
		Ret  : bool
		"""
		return linuxutil._cpuAffinity.set_cpu_affinity(cpus, self.pid)

	@property
	#@wrapException
	def getcpu(self):
		"""
		Desc : Get authorized cpu(s) 
		Args : None
		Ret  : bool
		"""
		return linuxutil._cpuAffinity.get_cpu_affinity(self.pid)

	#@wrapException
	def socket(self, fd = False):
		"""
		Desc : List of sockets inode
		Args : fd (False by default) to hide fd and True for show the number of the fd
		Ret  : List of Int if fd set to False or Dict
		"""
		if fd == True :
			return dict([(_k, int(_v['name'])) for _k, _v  in self.fd.items() if _v['type'] == 'socket'])
		else :
			return [int(_x['name']) for _x  in self.fd.values() if _x['type'] == 'socket']

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re
from linuxutil._common import *

_diskPath = '/sys/block/'
_virtualDiskPath = '/sys/devices/virtual/block'
_procMounts = '/proc/mounts'
_fstab = '/etc/fstab'

#@wrapException
def ls(all = False): 
	"""
	Desc : list disk
	Args : all (bool) => False for hide devices with null size
	Ret  : List
	"""
	if all == True:
		return [_x for _x in os.listdir(_diskPath) if not re.match('^sr[09]+$',_x)]
	else:
		return [_x for _x in os.listdir(_diskPath) if not re.match('^sr[09]+$',_x) and int(open(os.path.join(_diskPath, _x, 'size')).readline().strip()) != 0]

#@wrapException
def virtual(all = False):
	"""
	Desc : List virtal disk
	Args : all (bool) => False for hide devices with null size
	Ret  : List
	"""
	if all == True:
		return [_x for _x in os.listdir(_virtualDiskPath)]
	else:
		return [_x for _x in os.listdir(_virtualDiskPath) if int(open(os.path.join(_diskPath, _x, 'size')).readline().strip()) != 0]

#@wrapException
def physical():
	"""
	Desc : List physical disk
	Args : None
	Ret  : List
	"""
	return list(set(ls()).difference(virtual()))

#@wrapException
def dm():
	"""
	Desc : List device-mapper disk
	Args : None
	Ret  : List
	"""
	return [_x for _x in os.listdir(_diskPath) if os.path.isdir(os.path.join(_diskPath, _x, 'dm'))]

def partition_size(partition):
	_x = os.statvfs(partition)
	return {'f_bsize':_x[0], 'f_frsize':_x[1],'f_blocks':_x[2],'f_bfree':_x[3],'f_bavail':_x[4],'f_files':_x[5],'f_ffree':_x[6],'f_favail':_x[7],'f_flag':_x[9],'f_namemax':_x[9],}

def mount():
	"""
	Desc : List mountpoints
	Args : None
	Ret  : List of dict
	"""
	return [{'dev':_x.split()[0], 'mountpoint':_x.split()[1], 'fstype':_x.split()[2], 'options':_x.split()[3], 'freq':_x.split()[4], 'passno':_x.split()[5]} for _x in open(_procMounts).readlines()]

#@wrapException
def fstab():
	"""
	Desc : List mountpoints
	Args : None
	Ret  : List of dict
	"""
	return [{'dev':_x.split()[0], 'mountpoint':_x.split()[1], 'fstype':_x.split()[2], 'options':_x.split()[3], 'freq':_x.split()[4], 'passno':_x.split()[5]} for _x in open(_fstab).readlines() if not re.match('^\s*#', _x)]

#@wrapException
def fstab_not_mounted():
	"""
	Desc : Present in /etc/fstab but not mounted
	Args : None
	Ret  : List of Dict
	"""
	tab = []
	for i in fstab():
		if re.match('^swap$', i['fstype']) or re.match('^usbfs$', i['fstype']):
			continue
		found = False
		for j in mount():
			if i['mountpoint'] == j['mountpoint']:
				found = True
		if found == False:
			tab.append(i)
	return tab

class name:
	"""
	Desc : Represents a disk name
	Type : Class
	Ret  : Object
	Link : http://www.kernel.org/doc/Documentation/block/
	"""

	def __init__(self, name):
		"""
		Desc : Create a new disk object, raises OSError if the name does not exist
		Args : name (string)
		Ret  : Objet
		"""
		self.name = str(name)
		self.path = '/sys/block/%s' % self.name
		
		if self.name not in ls(all = True):
			raise OSError("No such disk found with name %s" % self.name)
			
		if os.path.exists(os.path.join(self.path, 'device')) and not re.match('c[0-9]+d[0-9]+', os.readlink(os.path.join(self.path, 'device')).split(os.sep)[-1]):
			self.dev = device(self.name)

		if os.path.exists(os.path.join(self.path, 'queue')):
			self.queue = queue(self.name)
	
	@property
	#@wrapException
	def is_virtual(self):
		"""
		Desc : Is a virtal disk ?
		Args : None
		Ret  : Bool
		"""
		return self.name in virtual()
		
	@property
	#@wrapException
	def is_physical(self):
		"""
		Desc : Is a physical disk ?
		Args : None
		Ret  : Bool
		"""
		return self.name in physical()
		
	@property
	#@wrapException
	def is_dm(self):
		"""
		Desc : Is a device-mapper disk ?
		Args : None
		Ret  : Bool
		"""
		return self.name in dm()

	@property
	#@wrapException
	def ls_partition(self):
		"""
		Desc : Show the disk partitions
		Args : None
		Ret  : String
		"""
		return [_x for _x in os.listdir(self.path) if _x.startswith(self.name)]
		
	@property
	#@wrapException
	def devpath(self):
		"""
		Desc : Show the disk path in /dev
		Args : None
		Ret  : String
		"""
		return "/dev/%s" % [_x.split('=')[1].strip() for _x in open(os.path.join(self.path, 'uevent')).readlines() if _x.startswith('DEVNAME')][0]

	@property
	#@wrapException
	def syspath(self):
		"""
		Desc : Show the disk path in /dev
		Args : None
		Ret  : String
		"""
		return os.path.realpath(self.path)
		
	@property
	#@wrapException
	def type(self):
		"""
		Desc : Type
		Args : None
		Ret  : String
		"""
		return "/dev/%s" % [_x.split('=')[1].strip() for _x in open(os.path.join(self.path, 'uevent')).readlines() if _x.startswith('DEVTYPE')][0]

	@property
	#@wrapException
	def slave(self):
		"""
		Desc : Show the slaves paths (multipath)
		Args : None
		Ret  : List
		"""
		return [_x for _x in os.listdir(os.path.join(self.path, 'slaves'))]
		
	@property
	#@wrapException
	def numslave(self):
		"""
		Desc : Count the slaves paths (multipath)
		Args : None
		Ret  : Int
		"""
		return len(self.slave)
		
	#@wrapException
	def slave_o(self):
		"""
		Desc : Object list of the muktipath disk name (multipath)
		Args : disk (string)
		Ret  : List of object(s)
		"""
		return [name(_x) for _x in os.listdir(os.path.join(self.path, 'slaves'))]
	
	@property
	#@wrapException
	def depend(self):
		"""
		Desc : Show the parent(s) path(s) (multipath)
		Args : None
		Ret  : List
		"""
		return [_x for _x in os.listdir(os.path.join(self.path, 'holders'))]
		
	@property
	#@wrapException
	def numdepend(self):
		"""
		Desc : Count the parent(s) path(s)
		Args : None
		Ret  : Int
		"""
		return len(self.depend)
	
	@property
	#@wrapException
	def depend_o(self):
		"""
		Desc : Object list of the parent(s) disk name (multipath)
		Args : None
		Ret  : List of object(s)
		"""
		return [name(_x) for _x in os.listdir(os.path.join(self.path, 'holders'))]
	
	@property
	#@wrapException
	def size(self):
		"""
		Desc : Size of the disk
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'size')).readline().strip())

	@property
	#@wrapException
	def dev(self):
		"""
		Desc : Major / Minor number of the device
		Args : None
		Ret  : List
		"""
		return {'major':int(open(os.path.join(self.path, 'dev')).readline().strip().split(':')[0]), 'minor':int(open(os.path.join(self.path, 'dev')).readline().strip().split(':')[1])}

	@property
	#@wrapException
	def alignment_offset(self):
		"""
		Desc : /sys/block/<disk>/alignment_offset
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'alignment_offset')).readline().strip())
		
	@property
	#@wrapException
	def capability(self):
		"""
		Desc : /sys/block/<disk>/capability
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'capability')).readline().strip())
		
	@property
	#@wrapException
	def discard_alignment(self):
		"""
		Desc : /sys/block/<disk>/discard_alignment
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'discard_alignment')).readline().strip())
		
	@property
	#@wrapException
	def ext_range(self):
		"""
		Desc : /sys/block/<disk>/ext_range
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'ext_range')).readline().strip())
		
	@property
	#@wrapException
	def removable(self):
		"""
		Desc : /sys/block/<disk>/removable
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'removable')).readline().strip())
		
	@property
	#@wrapException
	def ro(self):
		"""
		Desc : /sys/block/<disk>/ro
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'ro')).readline().strip())

	@property
	#@wrapException
	def inflight(self):
		"""
		Desc : /sys/block/<disk>/inflight
		Args : None
		Ret  : List
		"""
		return int(open(os.path.join(self.path, 'inflight')).readline().split())
		
	@property
	#@wrapException
	def stat(self):
		"""
		Desc : /sys/block/<disk>/stat
		Args : None
		Ret  : Dict of Int
		Link : http://www.kernel.org/doc/Documentation/block/stat.txt
		Name            units         description
		----            -----         -----------
		r_io            requests      number of read I/Os processed
		r_merges        requests      number of read I/Os merged with in-queue I/O
		r_sectors       sectors       number of sectors read
		r_ticks         milliseconds  total wait time for read requests
		w_io            requests      number of write I/Os processed
		w_merges        requests      number of write I/Os merged with in-queue I/O
		w_sectors       sectors       number of sectors written
		w_ticks         milliseconds  total wait time for write requests
		in_flight       requests      number of I/Os currently in flight
		io_ticks        milliseconds  total time this block device has been active
		time_in_queue   milliseconds  total wait time for all requests

		r_io, w_io
		=====================
		These values increment when an I/O request completes.

		r_merges, w_merges
		=========================
		These values increment when an I/O request is merged with an already-queued I/O request.

		r_sectors, w_sectors
		===========================
		These values count the number of sectors read from or written to this
		block device.  The "sectors" in question are the standard UNIX 512-byte
		sectors, not any device- or filesystem-specific block size.  The
		counters are incremented when the I/O completes.

		r_ticks, w_ticks
		=======================
		These values count the number of milliseconds that I/O requests have
		waited on this block device.  If there are multiple I/O requests waiting,
		these values will increase at a rate greater than 1000/second; for
		example, if 60 read requests wait for an average of 30 ms, the read_ticks
		field will increase by 60*30 = 1800.

		in_flight
		=========
		This value counts the number of I/O requests that have been issued to
		the device driver but have not yet completed.  It does not include I/O
		requests that are in the queue but not yet issued to the device driver.

		io_ticks
		========
		This value counts the number of milliseconds during which the device has
		had I/O requests queued.

		time_in_queue
		=============
		This value counts the number of milliseconds that I/O requests have waited
		on this block device.  If there are multiple I/O requests waiting, this
		value will increase as the product of the number of milliseconds times the
		number of requests waiting (see "read ticks" above for an example).
		"""
		return [{'r_io':int(_x.split()[0]), 'r_merges':int(_x.split()[1]), 'r_sectors':int(_x.split()[2]), 'r_ticks':int(_x.split()[3]), 'w_io':int(_x.split()[4]), 'w_merges':int(_x.split()[5]), 'w_sectors':int(_x.split()[6]), 'r_ticks':int(_x.split()[7]), 'in_flight':int(_x.split()[8]), 'io_ticks':int(_x.split()[9]), 'time_in_queue':int(_x.split()[10])} for _x in open(os.path.join(self.path, 'stat')).readlines()]
		#return [int(_x) for _x in open(os.path.join(self.path, 'stat')).readline().split()]
		

class device:
	"""
	Desc : Represents disk device attributes
	Type : Class
	Ret  : Object
	"""

	def __init__(self, name):
		"""
		Desc : Create a new disk device attribute object
		Args : name (string)
		Ret  : Objet
		"""
		self.name = str(name)
		self.path = '/sys/block/%s/device' % self.name
			
		if not os.path.exists(self.path) or re.match('c[0-9]+d[0-9]+', self.id):
			raise OSError("Not compatible with disk %s !" % self.name)

	@property
	#@wrapException
	def id(self):
		"""
		Desc : Id of the path
		Args : None
		Ret  : String
		"""
		return os.readlink(self.path).split(os.sep)[-1]
		
	@property
	#@wrapException
	def driver(self):
		"""
		Desc : Driver of the disk
		Args : None
		Ret  : String
		"""
		try:
			return os.readlink(os.path.join(self.path, 'driver')).split(os.sep)[-1]
		except OSError:
			return None
		
	@property
	#@wrapException
	def generic(self):
		"""
		Desc : Generic name of the disk
		Args : None
		Ret  : String
		"""
		try:
			return os.readlink(os.path.join(self.path, 'generic')).split(os.sep)[-1]
		except OSError:
			return None
	
	@property
	#@wrapException
	def device_blocked(self):
		"""
		Desc : /sys/block/<disk>/device/device_blocked
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'device_blocked')).readline().strip())
		
	@property
	#@wrapException
	def dh_state(self):
		"""
		Desc : /sys/block/<disk>/device/dh_state
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'dh_state')).readline().strip())
		
	@property
	#@wrapException
	def evt_media_change(self):
		"""
		Desc : /sys/block/<disk>/device/evt_media_change
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'evt_media_change')).readline().strip())
		
	@property
	#@wrapException
	def io(self):
		"""
		Desc : /sys/block/<disk>/device/iocounterbits
		Args : None
		Ret  : Dict
		"""
		return {'counterbits':int(open(os.path.join(self.path, 'iocounterbits')).readline().strip()), 'done_cnt':open(os.path.join(self.path, 'iocounterbits')).readline().strip(), 'err_cnt':open(os.path.join(self.path, 'ioerr_cnt')).readline().strip(), 'request_cnt':open(os.path.join(self.path, 'iorequest_cnt')).readline().strip()}

	@property
	#@wrapException
	def modalias(self):
		"""
		Desc : /sys/block/<disk>/device/modalias
		Args : None
		Ret  : String
		"""
		return open(os.path.join(self.path, 'modalias')).readline().strip()
	
	@property
	#@wrapException
	def model(self):
		"""
		Desc : Model controler of the the disk
		Args : None
		Ret  : String
		"""
		return open(os.path.join(self.path, 'model')).readline().strip()
		
	@property
	#@wrapException
	def vendor(self):
		"""
		Desc : Vendor of the the disk controler
		Args : None
		Ret  : String
		"""
		return open(os.path.join(self.path, 'vendor')).readline().strip()

	@property
	#@wrapException
	def queue_depth(self):
		"""
		Desc : /sys/block/<disk>/device/queue_depth
		Args : None
		Ret  : String
		"""
		return open(os.path.join(self.path, 'queue_depth')).readline().strip()
		
	@property
	#@wrapException
	def queue_type(self):
		"""
		Desc : /sys/block/<disk>/device/queue_type
		Args : None
		Ret  : String
		"""
		return open(os.path.join(self.path, 'queue_type')).readline().strip()
		
	@property
	#@wrapException
	def rev(self):
		"""
		Desc : Revision of the controler
		Args : None
		Ret  : String
		"""
		return open(os.path.join(self.path, 'rev')).readline().strip()

	@property
	#@wrapException
	def scsi_level(self):
		"""
		Desc : /sys/block/<disk>/device/scsi_level
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'scsi_level')).readline().strip())
		
	@property
	#@wrapException
	def state(self):
		"""
		Desc : State of the controler
		Args : None
		Ret  : String
		"""
		return open(os.path.join(self.path, 'state')).readline().strip()
		
	@property
	#@wrapException
	def timeout(self):
		"""
		Desc : /sys/block/<disk>/device/timeout
		Args : None
		Ret  : String
		"""
		return int(open(os.path.join(self.path, 'timeout')).readline().strip())
		
	@property
	#@wrapException
	def tpgs(self):
		"""
		Desc : /sys/block/<disk>/device/tpgs
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'tpgs')).readline().strip())

	@property
	#@wrapException
	def type(self):
		"""
		Desc : /sys/block/<disk>/device/tpgs
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'type')).readline().strip())

class queue:
	"""
	Desc : Queue attributes of the disk
	Type : Class
	Ret  : Object
	"""

	def __init__(self, name):
		"""
		Desc : Queue disk attributes
		Args : name (string)
		Ret  : Objet
		"""
		self.name = str(name)
		self.path = '/sys/block/%s/queue' % self.name

		if not os.path.exists(os.path.join(self.path)):
			raise OSError("Not compatible with disk %s !" % self.name)

	@property
	#@wrapException
	def add_random(self):
		"""
		Desc : /sys/block/<disk>/queue/add_random
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'add_random')).readline().strip())


	@property
	#@wrapException
	def discard_max_bytes(self):
		"""
		Desc : /sys/block/<disk>/queue/discard_max_bytes
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'discard_max_bytes')).readline().strip())
		
	@property
	#@wrapException
	def hw_sector_size(self):
		"""
		Desc : /sys/block/<disk>/queue/hw_sector_size
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'hw_sector_size')).readline().strip())
		
	@property
	#@wrapException
	def iostats(self):
		"""
		Desc : /sys/block/<disk>/queue/iostats
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'iostats')).readline().strip())
		
	@property
	#@wrapException
	def max_hw_sectors_kb(self):
		"""
		Desc : /sys/block/<disk>/queue/max_hw_sectors_kb
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'max_hw_sectors_kb')).readline().strip())

	@property
	#@wrapException
	def max_sectors_kb(self):
		"""
		Desc : /sys/block/<disk>/queue/max_sectors_kb
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'max_sectors_kb')).readline().strip())

	@property
	#@wrapException
	def max_segment_size(self):
		"""
		Desc : /sys/block/<disk>/queue/max_segment_size
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'max_segment_size')).readline().strip())
		
	@property
	#@wrapException
	def nomerges(self):
		"""
		Desc : /sys/block/<disk>/queue/nomerges
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'nomerges')).readline().strip())

	@property
	#@wrapException
	def optimal_io_size(self):
		"""
		Desc : /sys/block/<disk>/queue/optimal_io_size
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'optimal_io_size')).readline().strip())
		
	@property
	#@wrapException
	def read_ahead_kb(self):
		"""
		Desc : /sys/block/<disk>/queue/read_ahead_kb
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'read_ahead_kb')).readline().strip())

	@property
	#@wrapException
	def rq_affinity(self):
		"""
		Desc : /sys/block/<disk>/queue/rq_affinity
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'read_ahead_kb')).readline().strip())

	@property
	#@wrapException
	def discard_granularity(self):
		"""
		Desc : /sys/block/<disk>/queue/discard_granularity
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'discard_granularity')).readline().strip())

	@property
	#@wrapException
	def discard_zeroes_data(self):
		"""
		Desc : /sys/block/<disk>/queue/discard_zeroes_data
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'discard_zeroes_data')).readline().strip())

	@property
	#@wrapException
	def logical_block_size(self):
		"""
		Desc : /sys/block/<disk>/queue/logical_block_size
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'logical_block_size')).readline().strip())

	@property
	#@wrapException
	def max_integrity_segments(self):
		"""
		Desc : /sys/block/<disk>/queue/max_integrity_segments
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'max_integrity_segments')).readline().strip())

	@property
	#@wrapException
	def max_segments(self):
		"""
		Desc : /sys/block/<disk>/queue/max_segments
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'max_segments')).readline().strip())
		
	@property
	#@wrapException
	def minimum_io_size(self):
		"""
		Desc : /sys/block/<disk>/queue/minimum_io_size
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'minimum_io_size')).readline().strip())

	@property
	#@wrapException
	def nr_requests(self):
		"""
		Desc : /sys/block/<disk>/queue/nr_requests
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'nr_requests')).readline().strip())

	@property
	#@wrapException
	def physical_block_size(self):
		"""
		Desc : /sys/block/<disk>/queue/physical_block_size
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'physical_block_size')).readline().strip())

	@property
	#@wrapException
	def rotational(self):
		"""
		Desc : /sys/block/<disk>/queue/rotational
		Args : None
		Ret  : Int
		"""
		return int(open(os.path.join(self.path, 'rotational')).readline().strip())

	@property
	#@wrapException
	def scheduler(self):
		"""
		Desc : IO scheduler of the disk
		Args : None
		Ret  : Int
		"""
		return open(os.path.join(self.path, 'scheduler')).readline().strip().split('[')[1].split(']')[0]

	@property
	#@wrapException
	def ls_scheduler(self):
		"""
		Desc : Available IO schedulers
		Args : None
		Ret  : List
		"""
		return open(os.path.join(self.path, 'scheduler')).readline().strip().replace('[','').replace(']','').split()

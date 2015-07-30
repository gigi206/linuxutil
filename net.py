#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, socket, re, fcntl, struct, base64
from linuxutil._common import *

_procNet = os.path.join(ProcessPath,'net')

_tcp4 = [socket.AF_INET, socket.SOCK_STREAM, os.path.join(_procNet,'tcp')]
_tcp6 = [socket.AF_INET6, socket.SOCK_STREAM, os.path.join(_procNet,'tcp6')]
_udp4 = [socket.AF_INET, socket.SOCK_DGRAM, os.path.join(_procNet,'udp')]
_udp6 = [socket.AF_INET6, socket.SOCK_DGRAM, os.path.join(_procNet,'udp6')]
_udplite4 = [socket.AF_INET, socket.SOCK_DGRAM, os.path.join(_procNet,'udplite')]
_udplite6 = [socket.AF_INET6, socket.SOCK_DGRAM, os.path.join(_procNet,'udplite6')]

_familymap = {
	socket.AF_INET: 'IPV4',
	socket.AF_INET6: 'IPV6'
}

_protomap = {
	socket.SOCK_STREAM: 'TCP',
	socket.SOCK_DGRAM: 'UDP'
}

_netmap = {
	'all': [_tcp4, _tcp6, _udp4, _udp6, _udplite4, _udplite6],
	'tcp': [_tcp4, _tcp6],
	'tcp4': [_tcp4],
	'tcp6': [_tcp6],
	'udp': [_udp4, _udp6, _udplite4, _udplite6],
	'udp4': [_udp4, _udplite4],
	'udp6': [_udp6, _udplite6],
	'inet': [_tcp4, _tcp6, _udp4, _udp6, _udplite4, _udplite6],
	'inet4': [_tcp4, _udp4, _udplite4],
	'inet6': [_tcp6, _udp6, _udplite6]
}

#See /usr/src/linux-<version>/include/net/tcp_states.h in kernel source
_statemap = {
	'01': 'ESTABLISHED',
	'02': 'SYN_SENT',
	'03': 'SYN_RECV',
	'04': 'FIN_WAIT1',
	'05': 'FIN_WAIT2',
	'06': 'TIME_WAIT',
	'07': 'CLOSE',
	'08': 'CLOSE_WAIT',
	'09': 'LAST_ACK',
	'0A': 'LISTEN',
	'0B': 'CLOSING'
}

#@wrapException
def isipv6():
	"""
	Desc : Is ipv6 supported by the server ?
	Args : None
	Ret  : Bool
	"""
	if os.path.exists(_tcp6[2]):
		return True
	else:
		return False

#@wrapException
def decodeaddr(addr, family = 'auto'):
	"""
	Desc : Is ipv6 supported by the server ?
	Args :	* addr : ipv4 or ipv6 (base 16)
		* family :	-> socket.AF_INET to force ipv4
				-> socket.AF_INET6 to force ipv6
				-> auto for automatic recognition between ipv4 and ipv6
	Ret  : 	* string if addr is only an address
		* tuple if addr is an address with a port
	"""
	if family == 'auto':
		if len(addr) == 8:
			family = socket.AF_INET
		else:
			family = socket.AF_INET6
	
	if family == socket.AF_INET6 and not socket.has_ipv6:
		raise SystemError('Python must supports IPV6, please recompile python with IPV6 flag')
	
	count = addr.count(':')
	
	if count == 0:
		_ip = addr
	elif count == 1:
		_ip, _port = addr.split(':')
		_port = int(_port, 16)
	
	_ip = _ip.upper()
	
	if family == socket.AF_INET:  #IPV4
		_ip = _ip.encode('ascii')
		if sys.byteorder == 'little':
			_ip = socket.inet_ntop(family, base64.b16decode(_ip)[::-1])
		else:
			_ip = socket.inet_ntop(family, base64.b16decode(_ip))
	else:  #IPv6
		_ip = ip6convertshort(_ip)
	
	if count == 0:
		return _ip
	else:
		return (_ip, _port)

#@wrapException
def ip6convertshort(ip6):
	"""
	Desc : Convert an ipv6 in a short format
	Args : an ipv6 in base 16 format
	Ret  : string
	"""
	#if sys.byteorder == 'little':
		#return socket.inet_ntop(socket.AF_INET6, struct.pack('>4I', *struct.unpack('<4I', ip6)))
	#else:
		#return socket.inet_ntop(socket.AF_INET6, struct.pack('<4I', *struct.unpack('<4I', ip6)))
	return socket.inet_ntop(socket.AF_INET6, struct.pack('=4I', *struct.unpack('=4I', base64.b16decode(ip6.upper().encode()))))
		
#@wrapException
def resolvname(ip):
	"""
	Desc : Convert an ip to dns
	Args : ip (0.0.0.0)
	Ret  : string
	"""
	try:
		return socket.gethostbyaddr(ip)[0]
	except:
		return ip

#@wrapException
def connections(net = 'inet', dns = False, inode = False, user = False, filterUser = None):
	"""
	Desc : List network connections
	Args :	* net :		- all	  : list all connections
				- inet	  : ipv6 (tcp/udp) + ipv4 (tcp/udp) (default)
				- inet4	  : ipv4 (tcp + udp)
				- inet6	  : ipv6 (tcp + udp)
				- tcp	  : ipv4 (tcp) + ipv6 (tcp)
				- tcp4	  : ipv4 (tcp)
				- tcp6	  : ipv6 (tcp)
				- udp	  : ipv4 (udp) + ipv6 (udp)
				- udp4	  : ipv4 (udp)
				- udp6	  : ipv6 (udp)
		* dns :		- True	  : resolv ip in name
				- False	  : ip (default)
		* inode :	- True	  : resolv inode in name of the process
				- False	  : inode (default)
		* user : 	- True	  : resolv uid in user name
				- False	  : uid
		* filterUser 	- <uid>	  : filter resullts by uid if user == False
				- <username> : filter results by username if user == True
	Ret  : Array
	
	Exemples : 
		-connections(dns = True, inode = True, user = True, filterUser = 'root')
		-connections(net = 'tcp', filterUser = '0')
	"""
	
	if net not in _netmap:
		return False
	_y = []
	
	for _netpath in _netmap[net]:
		if not os.path.exists(_netpath[2]):
			continue
		
		for _x in [_x.split() for _x in open(_netpath[2]).readlines()][1:]:
			_localIP, _localPort = decodeaddr(_x[1] ,_netpath[0])
			_remoteIP, _remotePort = decodeaddr(_x[2] ,_netpath[0])

			if user == True:
				import pwd
				try: 
					_x[7] = pwd.getpwuid(int(_x[7]))[0]
				except:
					pass
			
			if filterUser != None and _x[7] != filterUser:
				continue
			
			
			#Can be slow but it's normal (the time to resolv ip by a DNS server)
			if dns == True:
				_localIP = resolvname(_localIP)
				_remoteIP = resolvname(_remoteIP)
			
			# Must be impoved (very bad performance)
			if inode == True:
				import linuxutil.pid as pid
				try:
					_x[9] = [pid.id(_z).name for _z in pid.ls() if int(_x[9]) in pid.id(_z).socket()][0]
				except:
					_x[9] = 'kernel'
					#pass
				
			#if len(_x) <= 12:
			#	for _i in range(5):
			#		_xappend(None)
				
			_y.append({
				'family': _familymap[_netpath[0]],
				'proto': _protomap[_netpath[1]],
				'sl': _x[0][:-1],
				'localIP': _localIP,
				'localPort': _localPort,
				'remoteIP': _remoteIP,
				'remotePort': _remotePort,
				'state': _statemap[_x[3]],
				'tx_queue': _x[4].split(':')[0],
				'rx_queue': _x[4].split(':')[1],
				#tr = timer
				#0  no timer is pending
				#1  retransmit-timer is pending
				#2  another timer (e.g. delayed ack or keepalive) is pending
				#3  this is a socket in TIME_WAIT state. Not all fields will contain data (or even exist)
				#4  zero window probe timer is pending
				'tr': _x[5].split(':')[0],
				'tr_timeout': _x[5].split(':')[1],
				'retrnsmt': _x[6],
				'uid': _x[7],
				'timeout': _x[8],
				'inode': _x[9],
				'refCount': _x[10],
				'memAddr': _x[11],
				#'retrnsmtTimeout': _x[12],
				#'predictedTick': _x[13],
				#'ack': _x[14],
				#'windowCongestion': _x[15],
				#'sizeThreshold': _x[16]
			})
	return _y

#@wrapException
def listen(net = 'inet', dns = False, inode = False, user = False, filterUser = None):
	"""
	Desc : 
	Return : Array of connections with LISTEN state
	Arguments : see connections function
	"""
	return [_x for _x in connections(net = net, dns = dns, inode = inode, user=user, filterUser = filterUser) if _x['state'] == 'LISTEN']

#@wrapException
def route(dns = False):
	if dns == True:
		return [{'iface': _x.split()[0],'dest': resolvname(decodeaddr(_x.split()[1])), 'gw': resolvname(decodeaddr(_x.split()[2])), 'flags': _x.split()[3], 'refCnt': _x.split()[4], 'use': _x.split()[5], 'metric': _x.split()[6], 'mask': resolvname(decodeaddr(_x.split()[7])), 'mtu': _x.split()[8], 'window': _x.split()[9], 'irtt': _x.split()[10]} for _x in open(os.path.join(_procNet,'route')).readlines()[1:]]	
	else:
		return [{'iface': _x.split()[0],'dest': decodeaddr(_x.split()[1]), 'gw': decodeaddr(_x.split()[2]), 'flags': _x.split()[3], 'refCnt': _x.split()[4], 'use': _x.split()[5], 'metric': _x.split()[6], 'mask': decodeaddr(_x.split()[7]), 'mtu': _x.split()[8], 'window': _x.split()[9], 'irtt': _x.split()[10]} for _x in open(os.path.join(_procNet,'route')).readlines()[1:]]	

#@wrapException
def route6(short = True):
	if short == True:
		return [{'dst': ip6convertshort(_x.split()[0]), 'dstMask': int(_x.split()[1], 16), 'src': ip6convertshort(_x.split()[2]), 'srcMask': int(_x.split()[3] ,16), 'nextHop': ip6convertshort(_x.split()[4]), 'distance': int(_x.split()[5], 16), 'refCnt': int(_x.split()[6]), 'use': int(_x.split()[7]), 'flags': _x.split()[8], 'iface': _x.split()[9]} for _x in open(os.path.join(_procNet,'ipv6_route'))]
	else:
		return [{'dst': _x.split()[0], 'dstMask': int(_x.split()[1], 16), 'src': _x.split()[2], 'srcMask': int(_x.split()[3] ,16), 'nextHop': _x.split()[4], 'distance': int(_x.split()[5], 16), 'refCnt': int(_x.split()[6]), 'use': int(_x.split()[7]), 'flags': _x.split()[8], 'iface': _x.split()[9]} for _x in open(os.path.join(_procNet,'ipv6_route'))]

#@wrapException
def gw(net = socket.AF_INET, dns = False):
	_x = [_x['gw'] for _x in route(dns = False) if _x if _x['dest'] == '0.0.0.0'][0]
	
	if dns == False:
		return _x
	else:
		return resolvname(_x)

#@wrapException
def arp(dns = False):
	#See /usr/include/linux/if_arp.h
	if dns == False:
		return [{'ip': _x.split()[0], 'type': _x.split()[1], 'flags': _x.split()[2], 'mac': _x.split()[3], 'mask': _x.split()[4], 'dev': _x.split()[5]} for _x in open(os.path.join(_procNet,'arp')).readlines()[1:]]
	else:
		return [{'ip': resolvname(_x.split()[0]), 'type': _x.split()[1], 'flags': _x.split()[2], 'mac': _x.split()[3], 'mask': _x.split()[4], 'dev': _x.split()[5]} for _x in open(os.path.join(_procNet,'arp')).readlines()[1:]]

#@wrapException
def ls():
	return os.listdir('/sys/class/net')
	
#@wrapException
def virtual():
	return os.listdir('/sys/devices/virtual/net')
	
#@wrapException
def physical():
	return list(set(ls()).difference(virtual()))
	
class dev:
	"""Represents an interface card"""

	def __init__(self, inet):
		self.name = inet
		self.path = '/sys/class/net/%s/' % self.name
		
		if inet not in ls():
			raise SystemError("%s is not a valid interface" % inet)
		
	@property
	#@wrapException
	def name(self):
		return self.name
	
	@property
	#@wrapException
	def ip(self):
		#See number in /usr/include/linux/sockios.h (SIOCGIFADDR = 0x8915)
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('=256s', str.encode(self.name)))[20:24])
		except:
			return None
		
	@property
	#@wrapException	
	def ip6(self):
		try:
			return ip6convertshort([_x.split()[0] for _x in open(os.path.join(_procNet, 'if_inet6')).readlines() if _x.split()[5] == self.name][0])
		except:
			return None

	@property
	#@wrapException	
	def mask6(self):
		try:
			return int([_x.split()[2] for _x in open(os.path.join(_procNet, 'if_inet6')).readlines() if _x.split()[5] == self.name][0], 16)
		except:
			return None
		
	@property
	#@wrapException
	def mask(self):
		#See number in /usr/include/linux/sockios.h (SIOCGIFNETMASK = 0x891b)
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x891b, struct.pack('=256s', str.encode(self.name)))[20:24])
		except:
			return None
		
		
	@property
	#@wrapException
	def broadcast(self):
		#See number in /usr/include/linux/sockios.h (SIOCGIFBRDADDR = 0x8919)
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8919, struct.pack('=256s', str.encode(self.name)))[20:24])
		except:
			return None
		
	@property
	#@wrapException
	def syspath(self):
		return os.path.realpath(self.path)
	
	@property
	#@wrapException
	def assigntype(self):
		return int(open(os.path.join(self.path, 'addr_assign_type')).read().strip())
		
	@property
	#@wrapException
	def mac(self):
		return open(os.path.join(self.path, 'address')).read().strip()
		
	
	@property
	#@wrapException
	def isplugged(self):
		"""Return True if a cable is plugged or False is not."""
		try:
			return bool(open(os.path.join(self.path,'carrier')).read().strip())
		except:
			return False
	
	@property
	#@wrapException
	def id(self):
		return open(os.path.join(self.path, 'dev_id')).read().strip()

	@property
	#@wrapException
	def dormant(self):
		if self.state == 'up':
			return int(open(os.path.join(self.path, 'dormant')).read().strip())
		else:
			return None
	
	@property
	#@wrapException
	def duplex(self):
		if self.isvirtual:
			return None
		else:
			return open(os.path.join(self.path, 'duplex')).read().strip()
	
	@property
	#@wrapException
	def speed(self):
		try:
			return int(open(os.path.join(self.path, 'speed')).read().strip())
		except:
			return None
	
	@property
	#@wrapException
	def alias(self):
		return open(os.path.join(self.path, 'ifalias')).read().strip()
	
	@property
	#@wrapException
	def index(self):
		return int(open(os.path.join(self.path, 'ifindex')).read().strip())
		
	@property
	#@wrapException
	def link(self):
		return int(open(os.path.join(self.path, 'iflink')).read().strip())

	@property
	#@wrapException
	def linkmode(self):
		return int(open(os.path.join(self.path, 'link_mode')).read().strip())
	
	@property
	#@wrapException
	def mtu(self):
		return int(open(os.path.join(self.path, 'mtu')).read().strip())
	
	@property
	#@wrapException
	def group(self):
		return int(open(os.path.join(self.path, 'netdev_group')).read().strip())
		
	@property
	#@wrapException
	def state(self):
		return open(os.path.join(self.path, 'operstate')).read().strip()
		
	@property
	#@wrapException
	def txqueuelen(self):
		return int(open(os.path.join(self.path, 'tx_queue_len')).read().strip())
	
	@property
	#@wrapException
	def type(self):
		return int(open(os.path.join(self.path, 'type')).read().strip())
	
	@property
	#@wrapException
	def vendorid(self):
		if self.isvirtual:
			return None
		else:
			return open(os.path.join(self.path, 'device', 'vendor')).read().strip()
	
	@property
	#@wrapException
	def deviceid(self):
		if self.isvirtual:
			return None
		else:
			return open(os.path.join(self.path, 'device', 'device')).read().strip()
	
	@property
	#@wrapException
	def subdeviceid(self):
		if self.isvirtual:
			return None
		else:
			return open(os.path.join(self.path, 'device', 'subsystem_device')).read().strip()
	
	@property
	#@wrapException
	def subvendorid(self):
		if self.isvirtual:
			return None
		else:
			return open(os.path.join(self.path, 'device', 'subsystem_vendor')).read().strip()
	
	@property
	#@wrapException
	def classid(self):
		if self.isvirtual:
			return None
		else:
			return open(os.path.join(self.path, 'device', 'class')).read().strip()
	
	@property
	#@wrapException
	def modalias(self):
		if self.isvirtual:
			return None
		else:
			return open(os.path.join(self.path, 'device', 'modalias')).read().strip()
	
	@property
	#@wrapException
	def localcpulist(self):
		if self.isvirtual:
			return None
		else:
			return open(os.path.join(self.path, 'device', 'local_cpulist')).read().strip()
	
	@property
	#@wrapException
	def localcpus(self):
		if self.isvirtual:
			return None
		else:
			return open(os.path.join(self.path, 'device', 'local_cpus')).read().strip()

	#@property
	#@wrapException
	#def pciId(self):
		#return os.path.basename(os.readlink(os.path.join(self.path, 'device')))
	
	@property
	#@wrapException
	def isenable(self):
		if self.isvirtual:
			return None
		else:
			return bool(open(os.path.join(self.path, 'device', 'enable')).read().strip())
	
	@property
	#@wrapException
	def irq(self):
		if self.isvirtual:
			return None
		else:
			return int(open(os.path.join(self.path, 'device', 'irq')).read().strip())

	@property
	#@wrapException
	def driver(self):
		if self.isvirtual:
			return None
		else:
			return os.path.basename(os.readlink(os.path.join(self.path, 'device', 'driver')))

	@property
	#@wrapException
	def classname(self):
		if self.isvirtual:
			return None
		else:
			import linuxutil.pci as pci
			return pci.classname(self.classid)
	
	@property
	#@wrapException
	def hwname(self):
		if self.isvirtual:
			return None
		else:
			import linuxutil.pci as pci
			vendorName, deviceName, subSystemName =  pci.pciname(self.vendorid, self.deviceid, self.subvendorid, self.subdeviceid)
			return {'vendor': vendorName, 'device': deviceName, 'subSystem': subSystemName}
	
	@property
	#@wrapException
	def isvirtual(self):
		return self.name in virtual()
		
	@property
	#@wrapException
	def is_physical(self):
		return self.name in physical()
	
	@property
	#@wrapException
	def collisions(self):
		return int(open(os.path.join(self.path, 'statistics', 'collisions')).read().strip())
	
	@property
	#@wrapException
	def multicast(self):
		return int(open(os.path.join(self.path, 'statistics', 'multicast')).read().strip())
	
	@property
	#@wrapException
	def rxbytes(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_bytes')).read().strip())
	
	@property
	#@wrapException
	def rxcompressed(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_compressed')).read().strip())
	
	@property
	#@wrapException
	def rxcrcerrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_crc_errors')).read().strip())
	
	@property
	#@wrapException
	def rxdropped(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_dropped')).read().strip())
	
	@property
	#@wrapException
	def rxerrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_errors')).read().strip())
	
	@property
	#@wrapException
	def rxfifoerrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_fifo_errors')).read().strip())
	
	@property
	#@wrapException
	def rxframeerrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_frame_errors')).read().strip())
	
	@property
	#@wrapException
	def rxlengtherrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_length_errors')).read().strip())
	
	@property
	#@wrapException
	def rxmissederrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_missed_errors')).read().strip())
	
	@property
	#@wrapException
	def rxovererrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_over_errors')).read().strip())
	
	@property
	#@wrapException
	def rxpackets(self):
		return int(open(os.path.join(self.path, 'statistics', 'rx_packets')).read().strip())
	
	@property
	#@wrapException
	def txabortederrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'tx_aborted_errors')).read().strip())
	
	@property
	#@wrapException
	def txbytes(self):
		return int(open(os.path.join(self.path, 'statistics', 'tx_bytes')).read().strip())
	
	@property
	#@wrapException
	def txcarriererrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'tx_carrier_errors')).read().strip())
	
	@property
	#@wrapException
	def txcompressed(self):
		return int(open(os.path.join(self.path, 'statistics', 'tx_compressed')).read().strip())
	
	@property
	#@wrapException
	def txdropped(self):
		return int(open(os.path.join(self.path, 'statistics', 'tx_dropped')).read().strip())
	
	@property
	#@wrapException
	def txerrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'tx_errors')).read().strip())
	
	@property
	#@wrapException
	def txfifoerrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'tx_fifo_errors')).read().strip())
	
	@property
	#@wrapException
	def txheartbeaterrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'tx_heartbeat_errors')).read().strip())
	
	@property
	#@wrapException
	def txpackets(self):
		return int(open(os.path.join(self.path, 'statistics', 'tx_packets')).read().strip())
	
	@property
	#@wrapException
	def txwindowerrors(self):
		return int(open(os.path.join(self.path, 'statistics', 'tx_window_errors')).read().strip())
	
	@property
	#@wrapException
	def pathid(self):
		"""
		Desc : Id of the path
		Args : None
		Ret  : String
		"""
		return os.path.realpath(os.path.join(self.path, 'device')).split('/')[-1]
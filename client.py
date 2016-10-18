###########################################
# CLIENT.PY
###########################################
# The client.py is the local "plugin" 
# or standalone app in the NetAudio suite.
# It captures local keyboard input and
# streams MIDI to the server to play
# remote instruments, then accepts and
# plays back the remote audio in real time.
###########################################
import os
import sys
import time
import base64
import cPickle
import datetime
import logging
import swmixer
import socket
import struct
import netmidi
import pyaudio
import datetime
import thread
import threading
import struct
import urllib2
import Queue
import numpy as np
import wave
from collections import deque
from pyfiglet import Figlet
from threading import Thread, currentThread, enumerate, Event, Lock, RLock
from getch import getch, pause
from subprocess import Popen, PIPE, STDOUT

logger = logging.getLogger('client')

# Logger
logging.basicConfig(
	format='%(asctime)s %(levelname)s %(message)s',
	filename='client_logs.log',
	level=logging.INFO,
	)


def load_instruments(patch):
	global notes
	WPATH = os.getcwd()
	INSTR = WPATH+'/wav/{}/'.format(patch)
	print 'hybrid inst', INSTR
	c = swmixer.Sound(INSTR+'/C.wav')
	d = swmixer.Sound(INSTR+'/D.wav')
	e = swmixer.Sound(INSTR+'/E.wav')
	f = swmixer.Sound(INSTR+'/F.wav')
	g = swmixer.Sound(INSTR+'/G.wav')

	notes = {'c': c, 'd': d, 'e': e, 'f': f, 'g': g}

# keyboard sends qwerty input
def record_send_note():
	tag = 0 
	while True:
		tag += 1
		note = getch()
		
		if DEBUG and note != 'q':
			print "[GTCH] %s with tag #%d at %s\n"%(note, tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
		
		key_event = struct.pack('si', note, tag)
		s.send(key_event)
		
		if note == 'q': 		# Here we send quit command to server and break record thread
			print 'pressed note', note
			break	
		
# keyboard plays qwerty input
def record_play_note():
	while True:
		note = getch()
		if note == 'q':
			break
		elif note in ['c','d','e','f','g']:
			notes[note].play()
			if DEBUG:
				print "Playing " + note

def hybrid_fork_note():

	"""
	we command mixer to play offset
	and after offset, play stream data from server 
	which is filled async in a separate thread
	"""

	global stop_stream
	global new_offset_evt
	global oframes

	tag = 0

	while True:
		if stop_stream:
			break

		tag += 1
		note = getch()
		if note in 'qQ':
			break

		elif note in ['c','d','e','f','g']:
			oframes = Queue.Queue()
			new_offset_evt.set()
			sndevt = notes[note].play(loffset=OFFSET, s_conn=s) 			# swmixer play
			key_event = struct.pack('si', note, tag)
			try:
				s.send(key_event)
			except socket.error, e:
				print e
				break
			
			if DEBUG:
				print "Playing & Sending " + note
	

def play_offset(hybrid_thread):
	global oframes

	try:
		while True:
			if not hybrid_thread.isAlive():
				break
			
			sck_data = np.fromstring( s.recv(sz * 2), dtype=np.int16 )
			if not np.count_nonzero(sck_data) == 0:
				oframes.put(sck_data, timeout=0.5)

	except socket.error, e:
		print e
		pass

	s.close()

def mixing(p):

	#
	# 	HERE IS EXAMPLE OF HOW TO MIX
	# 	THESE START & END SAMPLES EACH LOOP 
	#   -------------------------------------
	# 	head = np.fromstring(off_play, np.int16)  # from swmixer.tick()
	#	tail = np.fromstring(h, np.int16)   # from oframes.get()
	#	mix = np.add(head, tail) --> mixed amplitude values causes distortion
	# 	mix = mix.clip(-32000.0,32000.0) --> clip works on values not shape
	# 	fframe = struct.pack('h'*len(mix), *mix)
	# 	swmixer.gstream.write(fframe, CHUNK)

	while True:
		if not p.isAlive():
			break

		off_play, end = swmixer.tick()
		frame = None

		if off_play:	# client offset starts			
			frame = off_play
		
		if end and not oframes.empty(): 	# no need of end flag, as soon as server stream frames, start mixing
			h = oframes.get()
			srv_array = np.fromstring(h, np.int16)
			
			if len(srv_array) < sz: 	# This situation may be happen on remote, initially I found sample size between 30-60 in queue
				srv_array = np.append(srv_array, np.zeros(sz - len(srv_array), np.int16))

			frame = (srv_array.astype(np.int16)).tostring()

		if frame is not None:
			while swmixer.gstream.get_write_available() < CHUNK: time.sleep(0.001)
			swmixer.gstream.write(frame, CHUNK)
			
def get_server_latency(HOST):
	cmd = 'fping -e {host}'.format(host=HOST)
	try:
		p=Popen(cmd.split(' '), stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False).communicate()[0].strip() 		 # 0 -> result, 1-> error
		if p:
			try:
				return round(float(p[p.find("(")+1:p.find("ms")].strip()))
			except ValueError, e: 		# unreachable
				return 0
	except Exception, e:	# fping not installed
		return 0
		
	return 0

def splash():
	os.system('clear')
	f = Figlet(font='standard')
	print "\n\n\n"
	print f.renderText('-NETAUDIO-'),
	print "\t\t(c) 2016 Omnibot Holdings LLC"
	print "\n\n\n\n"
	time.sleep(1.0)

if __name__ == '__main__':

	CHUNK = 64
	CHANNELS = 2
	MODE = 'local'
	DEBUG = True
	OFFSET = 0
	PATCH = 'brass'
	oframes = Queue.Queue()
	OID = 2
	stop_stream = False
	HOST = '45.79.175.75'
	PORT = 12345
	glock = RLock()
	sz = CHUNK * CHANNELS
	new_offset_evt = Event()

	if DEBUG:
		print 'connect localhost'
		HOST = '127.0.0.1'

	splash()						# Render splash
	clear = os.system('clear')		# Clear screen
	MODE = netmidi.select_mode()
	if MODE and MODE in 'Qquit':
		quit()
	
	#input_id = netmidi.select_midi_device()

	try:

		if MODE == 'local':
			PATCH = netmidi.select_instrument()
		
			if PATCH is None:
				PATCH = 'piano'

			WPATH = '.'
			INSTR=WPATH+'/wav/'+PATCH

			# Create Mixer
			swmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)

			# Set Sounds
			c = swmixer.Sound(INSTR+'/C.wav')
			d = swmixer.Sound(INSTR+'/D.wav')
			e = swmixer.Sound(INSTR+'/E.wav')
			f = swmixer.Sound(INSTR+'/F.wav')
			g = swmixer.Sound(INSTR+'/G.wav')

			notes = {'c': c, 'd': d, 'e': e, 'f': f, 'g': g}

			swmixer.start()
			keys = Thread(target=record_play_note)  
			keys.start()


		elif MODE == 'remote':

			p = pyaudio.PyAudio()

			pstream = p.open(
				format = pyaudio.paInt16,
				channels = 2,
				rate = 44100,
				output = True)

			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			try:
				connect_res = s.connect_ex((HOST, PORT)) 		# conenct_ex return integer response, if response is greater than 0 there must be some error
			except socket.error, msg:
				if DEBUG:
					print "Could not connect with server."
					print msg

				quit()

			commands = cPickle.dumps((PATCH, DEBUG, OFFSET))
			s.send(commands)

			keys = Thread(target=record_send_note)	
			keys.start()

			stream = Thread(target=stream_incoming_odata, args=(keys,))
			stream.start()
			stream.join()

		elif MODE == 'hybrid':

			get_remote_latency = get_server_latency('45.79.175.75')
			print 'latency in ms: ', get_remote_latency
			if get_remote_latency is not None:
				# ADDED 100 frames to the offset, for overhead
				OFFSET = int(get_remote_latency)+100

			#### LOCAL PART

			swmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)
			load_instruments(PATCH)

			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.setblocking(1)
			try:
				connect_res = s.connect_ex((HOST, PORT))
			except socket.error, msg:
				if DEBUG:
					print "Could not connect with server."
					print msg
				quit()

			commands = cPickle.dumps((PATCH, DEBUG, OFFSET))
			
			try:
				s.send(commands)
			except socket.error, e:
				pass
			
			hybrid = Thread(target=hybrid_fork_note, name="hybrid")
			hybrid.start()

			play_off_tick = Thread(target=play_offset, name="play", args=(hybrid,))
			play_off_tick.start()

			mix_and_drain = Thread(target=mixing, name='mixing', args=(play_off_tick,))
			mix_and_drain.start()
			
			oframes.join()
			
		elif MODE == 'quit':
			quit()

		else:
			print 'Unknown selection'

	except KeyboardInterrupt, e:
		stop_stream = True
		sys.exit(1)


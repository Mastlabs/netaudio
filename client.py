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

	tag = 0

	while True:
		if stop_stream:
			break

		tag += 1
		note = getch()
		if note in 'qQ':
			break

		elif note in ['c','d','e','f','g']:
			sndevt = notes[note].play(loffset=OFFSET, s_conn=s) 			# swmixer play
			key_event = struct.pack('si', note, tag)
			try:
				s.send(key_event)
			except socket.error, e:
				print e
				break
			
			if DEBUG:
				print "Playing & Sending " + note
	
def off_tick(mix_str, sz):
	
	t = np.fromstring(mix_str, dtype=np.int16)	
	if np.count_nonzero(t) == 0:
		return None

	if len(t) < sz:
		t = np.append(t, np.zeros(sz - len(t), np.int16))
	
	return t

def play_offset(hybrid_thread):

	sz = CHUNK * CHANNELS
	try:
		while True:
			if not hybrid_thread.isAlive():
				break
			
			b = np.zeros(sz, np.float)
			off_play, end = swmixer.tick()
			
			glock.acquire()
			if off_play:
				b += off_tick(off_play, sz) 		# OFFSET mix
				srv_data, fr_num = wave.struct.unpack('256si', s.recv(260)) 		# 256 for odata and 4 bytes for integer
				if DEBUG:
					print('Stream frame number (per sample size - 128) #{}\n'.format(fr_num))
				oframes.put(srv_data)

			if end:
				srv_data, fr_num = wave.struct.unpack('256si', s.recv(260))
				if DEBUG:
					print('Stream frame number (per sample size - 128) #{}\n'.format(fr_num))

				oframes.put(srv_data)

			glock.release()

			if end and oframes: 		 # pop() after offset passes
				while not oframes.empty():
					h = oframes.get()
					d = off_tick(h, sz)
					if d is None:
						continue
					b += d 	# On second iteration of master loop, offset mix is ready as well as server mix is ready, we merge both of them by appending in numpy zero array (b)
				
			b = b.clip(-32767.0, 32767.0)
			odata = (b.astype(np.int16)).tostring()
			while swmixer.gstream.get_write_available() < CHUNK: time.sleep(0.001)
			swmixer.gstream.write(odata)
	
	except Exception, e:
		pass

	s.close()

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
	PATCH = 'piano'
	oframes = Queue.Queue()
	OID = 2
	stop_stream = False
	HOST = '45.79.175.75'
	PORT = 12345
	glock = Lock()

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
				OFFSET = int(get_remote_latency)

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
			
		elif MODE == 'quit':
			quit()

		else:
			print 'Unknown selection'

	except KeyboardInterrupt, e:
		stop_stream = True
		sys.exit(1)


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
import zlib
import numpy as np
from pyfiglet import Figlet
from threading import Thread, currentThread
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
	INSTR = WPATH+'/wav/'+patch
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
	tag = 0
	while True:
		tag += 1
		note = getch()
		if note == 'q':
			break
		elif note in ['c','d','e','f','g']:
			notes[note].play(loffset=OFFSET) 			# swmixer play
			key_event = struct.pack('si', note, tag)
			s.send(key_event)
			if DEBUG:
				print "Playing & Sending " + note
	
	s.close()

def stream_incoming_odata(send_note_thread):
	
	while True:
	
		if not send_note_thread.isAlive():
			s.close()
			break

		odata = s.recv(CHUNK * CHANNELS * 4)

		if DEBUG:
			# odata = base64.b64decode(odata) 		# decode binary buffer to b64
			# if 'data----' in odata:
			# 	try:
			# 		extra_str = odata[odata.find('data----'):odata.find('----data')]
			# 		note, tag = tuple(extra_str.split(':'))
			# 		print "[STRM] %s with tag #%s at %s"%(note.strip(), tag.strip(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
				
			# 	except Exception, e:	# Multiple value unpack error occurred if data is not base64 encoded
			# 		print e
				
			# 	odata = odata.replace(extra_str+'----data', '')
			pass

		if odata:
			pstream.write(odata)

def get_server_latency(HOST):
	cmd = 'fping -e {host}'.format(host=HOST)
	p=Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE).communicate()[0].strip() 		 # 0 -> result, 1-> error
	if p:
		print p
		try:
			return round(float(p[p.find("(")+1:p.find("ms")].strip()))
		except ValueError, e: 		# unreachable
			return None
		
	return None

def splash():
	os.system('clear')
	f = Figlet(font='standard')
	print "\n\n\n"
	print f.renderText('-NETAUDIO-'),
	print "\t\t(c) 2016 Omnibot Holdings LLC"
	print "\n\n\n\n"
	time.sleep(1.0)

if __name__ == '__main__':

	# HOST = '127.0.0.1'	
	HOST = '45.79.175.75'
	PORT = 12345

	CHUNK = 64
	CHANNELS = 2
	MODE = 'local'
	DEBUG = True
	OFFSET = 0
	PATCH = 'piano'
	
	splash()		# Render splash
	clear = os.system('clear')		# Clear screen
	MODE = netmidi.select_mode()
	if MODE in 'Qquit':
		quit()
	
	#input_id = netmidi.select_midi_device()

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

		get_remote_latency = get_server_latency(HOST)
		print 'latency', get_remote_latency
		if get_remote_latency is not None:
			OFFSET = int(get_remote_latency)

		#### LOCAL PART

		swmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)
		load_instruments(PATCH)
		swmixer.start()

		######## REMOTE PART

		p = pyaudio.PyAudio()
		pstream = p.open(
			format = pyaudio.paInt16,
			channels = 2,
			rate = 44100,
			output = True)

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			connect_res = s.connect_ex((HOST, PORT))
		except socket.error, msg:
			if DEBUG:
				print "Could not connect with server."
				print msg
			quit()

		commands = cPickle.dumps((PATCH, DEBUG, OFFSET))
		s.send(commands)
		
		keys = Thread(target=hybrid_fork_note)  
		keys.start()

		stream = Thread(target=stream_incoming_odata, args=(keys, ))
		stream.start()
		stream.join()

	elif MODE == 'quit':
		quit()

	else:
		print 'Unknown selection'

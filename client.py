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
import datetime
import logging
import pygame
import swmixer
import socket
import struct
import netmidi
import pyaudio
import sys
import time
import datetime
import json
import thread
import threading
import numpy as np
from pyfiglet import Figlet
from threading import Thread, currentThread
from getch import getch, pause
import base64
import ast

CHUNK = 64
CHANNELS = 2
MODE = 'local'

# setup socket
#HOST = ''
HOST = '45.79.175.75'
PORT = 12345
term = False

logger = logging.getLogger('client')
frames = []

swmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)

# Logger
logging.basicConfig(
	format='%(asctime)s %(levelname)s %(message)s',
	filename='client_logs.log',
	level=logging.INFO,
	)

# keyboard sends qwerty input
def record_send_note():
	global term
	tag = 0 
	while True:
		tag += 1
		note = getch()
		if note == 'q':
			s.close()
			term = True
			break
		
		print "[GTCH] %s with tag #%d at %s\n"%(note, tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
		key_event = struct.pack('si', note, tag)
		s.send(key_event)
	s.close()

# keyboard plays qwerty input
def record_play_note():
	while True:
		note = getch()
		if note == 'q':
			break
		elif note in ['c','d','e','f','g']:
			notes[note].play()
			#print "Playing " + note

def hybrid_fork_note():
	while True:
		note = getch()
		if note == 'q':
			break
		elif note in ['c','d','e','f','g']:
			notes[note].play()
			s.send(note)
			#print "Playing & Sending " + note
	s.close()

def stream_incoming_odata(): 
	while True:
		if term:
			break
		try:
			#odata = s.recv(CHUNK * CHANNELS * 2)
			odata = s.recv(300)
			
			if 'net' in odata or 'mixer' in odata:
				#print 'rcv odata' , len(odata)
				try:
					extra_str = odata[odata.find('net'):odata.find('mixer')]
					note, tag = tuple(extra_str.split(':'))
					print "[STRM] %s with tag #%s at %s"%(note.strip(), tag.strip(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
				except Exception, e:
					print e
				
				odata = odata.replace(extra_str+'mixer', '')
				#print 'after remove mods odata', len(odata)

		except socket.error, e:
			s.close()
			break
		
		if odata > CHUNK:
			pstream.write(odata)
			time.sleep(0.001)
			#logger.info('receive audio stream %s'% gdata)

def splash():
	os.system('clear')
	f = Figlet(font='standard')
	print "\n\n\n"
	print f.renderText('-NETAUDIO-'),
	print "\t\t(c) 2016 Omnibot Holdings LLC"
	print "\n\n\n\n"
	time.sleep(1.0)

if __name__ == '__main__':


	# Render splash

	splash()

	# Clear screen
	clear = os.system('clear')

	MODE = netmidi.select_mode()
	if MODE in 'Qquit':
		quit()
	#input_id = netmidi.select_midi_device()

	if MODE == 'local':
		PATCH = netmidi.select_instrument()
	
		if PATCH is None:
			PATCH = 'piano'

		#WPATH = '/Users/iakom/Developer/Mixer/'
		WPATH = '.'
		INSTR=WPATH+'/wav/'+PATCH

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
			s.connect((HOST, PORT))
		except socket.error, msg:
			print "Could not connect with server."
			print msg
			quit()

		keys = Thread(target=record_send_note)	
		keys.start()

		stream = Thread(target=stream_incoming_odata)
		stream.start()
		stream.join()


	elif MODE == 'hybrid':

		#### LOCAL PART

		PATCH = netmidi.select_instrument()
	
		if PATCH is None:
			PATCH = 'piano'

		#WPATH = '/Users/iakom/Developer/Mixer/'
		WPATH = '.'
		INSTR=WPATH+'/wav/'+PATCH

		# Set Sounds
		c = swmixer.Sound(INSTR+'/C.wav')
		d = swmixer.Sound(INSTR+'/D.wav')
		e = swmixer.Sound(INSTR+'/E.wav')
		f = swmixer.Sound(INSTR+'/F.wav')
		g = swmixer.Sound(INSTR+'/G.wav')

		notes = {'c': c, 'd': d, 'e': e, 'f': f, 'g': g}

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
			s.connect((HOST, PORT))
		except socket.error, msg:
			print "Could not connect with server."
			print msg
			quit()

		keys = Thread(target=hybrid_fork_note)  
		keys.start()

		stream = Thread(target=stream_incoming_odata)
		stream.start()
		stream.join()

		
	elif MODE == 'quit':
		quit()

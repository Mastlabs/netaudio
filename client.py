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
import datetime
import logging
import pygame
import swmixer
import socket
import struct
import netmidi
import pyaudio
import datetime
import json
import thread
import threading
import numpy as np
from pyfiglet import Figlet
from threading import Thread, currentThread
from getch import getch, pause

CHUNK = 64
CHANNELS = 2
MODE = 'local'
# DEBUG = False
DEBUG = True

# setup socket
# HOST = '0.0.0.0'
HOST = '45.79.175.75'
PORT = 12345
logger = logging.getLogger('client')
swmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)

# Logger
logging.basicConfig(
	format='%(asctime)s %(levelname)s %(message)s',
	filename='client_logs.log',
	level=logging.INFO,
	)

# keyboard sends qwerty input
def record_send_note():
	tag = 0 
	while True:
		tag += 1
		note = getch()
		
		if DEBUG and note != 'q':
			print "[GTCH] %s with tag #%d at %s\n"%(note, tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
		
		if note == 'q': 		# Here we send quit command to server and break record thread
			print 'pressed note', note
			break	
		
		key_event = struct.pack('si', note, tag)
		s.send(key_event)
		
		
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
	while True:
		note = getch()
		if note == 'q':
			break
		elif note in ['c','d','e','f','g']:
			notes[note].play()
			s.send(note)
			if DEBUG:
				print "Playing & Sending " + note
	
	s.close()

def stream_incoming_odata(send_note_thread):
	
	try:
		while True:
		
			if not send_note_thread.isAlive():
				'break it'
				s.close()
				break

			#data = s.recv(CHUNK * CHANNELS * 4)
			data = s.recv(CHUNK * CHANNELS * 2)
			odata = base64.b64decode(data) 		# decode binary buffer to b64
			
			if DEBUG:
				if 'data----' in odata:
					try:
						extra_str = odata[odata.find('data----'):odata.find('----data')]
						note, tag = tuple(extra_str.split(':'))
						print "[STRM] %s with tag #%s at %s"%(note.strip(), tag.strip(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
					
					except Exception, e:	# Multiple value unpack error occurred if data is not base64 encoded
						print e
					
					odata = odata.replace(extra_str+'----data', '')
					
			if odata:
				pstream.write(odata)

	except socket.error, e:
		if DEBUG:
			print e
		return
	
def splash():
	os.system('clear')
	f = Figlet(font='standard')
	print "\n\n\n"
	print f.renderText('-NETAUDIO-'),
	print "\t\t(c) 2016 Omnibot Holdings LLC"
	print "\n\n\n\n"
	time.sleep(1.0)

if __name__ == '__main__':

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
			connect_res = s.connect_ex((HOST, PORT)) 		# conenct_ex return integer response, if response is greater than 0 there must be some error
		except socket.error, msg:
			if DEBUG:
				print "Could not connect with server."
				print msg

			quit()

		keys = Thread(target=record_send_note)	
		keys.start()

		stream = Thread(target=stream_incoming_odata, args=(keys,))
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
			if DEBUG:
				print "Could not connect with server."
				print msg

			quit()

		keys = Thread(target=hybrid_fork_note)  
		keys.start()

		stream = Thread(target=stream_incoming_odata, args=(keys, ))
		stream.start()
		stream.join()

		
	elif MODE == 'quit':
		quit()

	else:
		print 'Unknown selection'


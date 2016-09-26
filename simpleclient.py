###########################################
# SIMPLECLIENT.PY
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
import collections
import socket
import pyaudio
import sys
import time
import wave
import numpy
import struct
import thread
import urllib2
import requests
from threading import Thread, currentThread
from getch import getch, pause

def set_debug(val):
	global DEBUG
	if val == False:
		DEBUG = False
	elif val == True:
		DEBUG = True

def set_offset(val):
	global OFF
	OFF = val

def load_instruments(patch):
	global c,d,e,f,g,notes

	LHOST = '127.0.0.1'

	INSTR = "http://"+LHOST+":8000/"+patch
	#WPATH = os.getcwd()
	#INSTR = WPATH+'/wav/'+patch

	cfile = wave.open(urllib2.urlopen(INSTR+'/C.wav'), 'r')
	dfile = wave.open(urllib2.urlopen(INSTR+'/D.wav'), 'r')
	efile = wave.open(urllib2.urlopen(INSTR+'/E.wav'), 'r')
	ffile = wave.open(urllib2.urlopen(INSTR+'/F.wav'), 'r')
	gfile = wave.open(urllib2.urlopen(INSTR+'/G.wav'), 'r')

	for i in range (0, cfile.getnframes()):
		c.append(cfile.readframes(CHUNK))

	for i in range (0, dfile.getnframes()):
		d.append(dfile.readframes(CHUNK))

	for i in range (0, efile.getnframes()):
		e.append(efile.readframes(CHUNK))

	for i in range (0, ffile.getnframes()):
		f.append(ffile.readframes(CHUNK))

	for i in range (0, gfile.getnframes()):
		g.append(gfile.readframes(CHUNK))
	
	notes = {'c':c, 'd':d, 'e':e, 'f':f, 'g':g}

def play_note(note):
	#j=1
	#note.rewind()
	#FEA = OFF - 60
	for i in range(OFF):
		frame = note[i]

		# if (i > FEA):
		# 	#print "DC OFFSET ===================="
		# 	s = numpy.fromstring(frame, numpy.int16)
		# 	#s = s.clip(-32000.0,32000.0)
		# 	s = s * j
		# 	frame = struct.pack('h'*len(s), *s)
		# 	j = j * 0.1

		hashd = hash(frame) 
		if hashd != 0:
			#print "START "+str(i)+":"+str(hashd)
			lstream.write(frame)
			#time.sleep(0.001)
	
	# I put the stream write out here vs. the other
	# thread to keep in lockstep since I was too
	# lazy to write a lock mechanism. Once we do,
	# this can move back into the stream thread.		

	while len(oframes) > 0:
		ndata = oframes.pop(0)
		hashf = hash(ndata)
		if hashf != 0:
			#print "END "+":"+str(hashf)
			lstream.write(ndata)
			#time.sleep(0.001)

def drain_stream():
	time.sleep(1.0)
	while len(oframes) > 0:
		ndata = oframes.pop(0)
		hashf = hash(ndata)
		if hashf != 0:
			#print "END "+":"+str(hashf)
			lstream.write(ndata)
			#time.sleep(0.001)

def send_notes():
	while True:
		note = getch()
		if note in 'qQ':
			print "Quitting"
			break
		# IF CAPS, REMOTE MODE
		elif note in ['C', 'D', 'E', 'F', 'G']:
			print "REMOTE NOTE"
			print "Wait..."
			s.send(note)
			drain_stream()
			print "Play."
		# IF LOWERCASE, HYBRID MODE
		elif note in ['c','d','e','f','g']:
			print "HYBRID NOTE"
			print "Wait..."
			s.send(note)
			play_note(notes[note])
			print "Play."
	quit()

def stream_audio():
	while True:
		odata = s.recv(CHUNK * CHANNELS * 2)
		oframes.append(odata)
		#ndata = oframes.pop(0)
		#rstream.write(ndata)
		#time.sleep(0.001)

if __name__ == '__main__':

	CHUNK = 64
	CHANNELS = 2
	OFF = 0
	OID = 1
	DEBUG = False
	oframes = []

	c = []
	d = []
	e = []
	f = []
	g = []

	notes = None

	# setup socket
	HOST = 'localhost'
	#HOST = '45.79.175.75'
	PORT = 12345

	# Clear screen
	clear = os.system('clear')

	# Initialize
	p = pyaudio.PyAudio()
	load_instruments('brass')
	set_offset(250)

	#for i in range(p.get_device_count()):
	#	print p.get_device_info_by_index(i)

	rstream = p.open(
		format = pyaudio.paInt16,
		channels = 2,
		rate = 44100,
		output = True)

	lstream = p.open(
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

	keys = Thread(target=send_notes)	
	keys.start()

	stream = Thread(target=stream_audio)
	stream.start()
	stream.join()

	quit()

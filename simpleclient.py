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
import socket
import pyaudio
import sys
import time
import wave
import numpy
import struct
import thread
import threading
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

	WPATH = os.getcwd()
	INSTR = WPATH+'/wav/'+patch

	c = wave.open(INSTR+'/C.wav', 'r')
	d = wave.open(INSTR+'/D.wav', 'r')
	e = wave.open(INSTR+'/E.wav', 'r')
	f = wave.open(INSTR+'/F.wav', 'r')
	g = wave.open(INSTR+'/G.wav', 'r')
	
	notes = {'c':c, 'd':d, 'e':e, 'f':f, 'g':g}

def play_note(note):
	j=2
	note.rewind()
	for i in range(OFF):
		frame = note.readframes(CHUNK)

		if (i > OFF - 10):
			#print "DC OFFSET ===================="
			s = numpy.fromstring(frame, numpy.int16)
			s = s.clip(-32000.0/j,32000.0/j)
			frame = struct.pack('h'*len(s), *s)
			j = j*4

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
			pass
			#print "END "+":"+str(hashf)
			rstream.write(ndata)
			#time.sleep(0.001)

def drain_stream():
	time.sleep(1.0)
	while len(oframes) > 0:
		ndata = oframes.pop(0)
		hashf = hash(ndata)
		if hashf != 0:
			pass
			#print "END "+":"+str(hashf)
			rstream.write(ndata)
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

	c = None
	d = None
	e = None
	f = None
	g = None

	notes = None

	# setup socket
	HOST = ''
	#HOST = '45.79.175.75'
	PORT = 12345

	# Clear screen
	clear = os.system('clear')

	# Initialize
	p = pyaudio.PyAudio()
	load_instruments('brass')
	set_offset(150)

	#for i in range(p.get_device_count()):
	#	print p.get_device_info_by_index(i)

	rstream = p.open(
		format = pyaudio.paInt16,
		channels = 2,
		rate = 44100,
		output = True,
		output_device_index=OID)

	lstream = p.open(
		format = pyaudio.paInt16,
		channels = 2,
		rate = 44100,
		output = True,
		output_device_index=OID)

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

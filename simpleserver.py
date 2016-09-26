############################################
# SIMPLESERVER.PY
############################################
# The server.py is the server component of
# the NetAudio prototype suite. It plays
# the remote instrumentss and streams iudio
# back to the local client.
############################################

import os
import sys
import time
import wave
import datetime
import socket
import numpy
import struct
from Queue import Queue
from threading import Thread, currentThread

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

	cfile = wave.open(INSTR+'/C.wav', 'r')
	dfile = wave.open(INSTR+'/D.wav', 'r')
	efile = wave.open(INSTR+'/E.wav', 'r')
	ffile = wave.open(INSTR+'/F.wav', 'r')
	gfile = wave.open(INSTR+'/G.wav', 'r')

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
	for i in range(OFF, len(note)):
		frame = note[i]
		hashd = hash(frame) 
		if hashd != 0:
			print "FIN "+str(i)+":"+str(hashd)
			conn.send(frame)

if __name__ == "__main__":

	CHUNK = 64
	CHANNELS = 2
	HOST = '0.0.0.0'
	PORT = 12345
	DEBUG = False
	OFF = 0 

	c = []
	d = []
	e = []
	f = []
	g = []

	notes = None

	# INITIALIZE
	load_instruments('piano')
	set_offset(250)

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
	s.bind((HOST, PORT))
	s.listen(5)

	global conn
	conn, addr = s.accept()

	os.system('clear')

	print "\nServer started..."

	while True:
		note = conn.recv(CHUNK * CHANNELS * 2)
		if note.istitle():
			note = note.lower()
			set_offset(0)
			play_note(notes[note])
		elif note in ['c','d','e','f','g']:
			#time.sleep(0.01)
			set_offset(250)
			play_note(notes[note])
		

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
from Queue import Queue
from threading import Thread, currentThread

CHUNK = 64
CHANNELS = 2
OFF = 100

WPATH = os.getcwd()
#INSTR=WPATH+'/wav/piano'
#INSTR=WPATH+'/wav/strings'
#INSTR=WPATH+'/wav/perc'
INSTR=WPATH+'/wav/brass'
#INSTR=WPATH+'/wav/glock'

def play_note(note):
	note.rewind()
	for j in range(note.getnframes()):
		frame = note.readframes(CHUNK)
		if j < OFF:
			continue
		hashd = hash(frame) 
		if hashd != 0:
			print "FIN "+str(j)+":"+str(hashd)
			conn.send(frame)

if __name__ == "__main__":

	HOST = '0.0.0.0'
	PORT = 12345

	c = wave.open(INSTR+'/C.wav', 'r')
	d = wave.open(INSTR+'/D.wav', 'r')
	e = wave.open(INSTR+'/E.wav', 'r')
	f = wave.open(INSTR+'/F.wav', 'r')
	g = wave.open(INSTR+'/G.wav', 'r')

	notes = {'c':c, 'd':d, 'e':e, 'f':f, 'g':g}

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
		if note in ['c','d','e','f','g']:
			#time.sleep(0.01)
			play_note(notes[note])

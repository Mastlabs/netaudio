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
import thread
import threading
from threading import Thread, currentThread
from getch import getch, pause

CHUNK = 64
CHANNELS = 2
MODE = 'local'
OFF = 200
oframes = []

# setup socket
#HOST = ''
HOST = '45.79.175.75'
PORT = 12345

def play_note(note):
	note.rewind()
	for i in range(OFF):
		frame = note.readframes(CHUNK)
		hashd = hash(frame) 
		if hashd != 0:
			print "STR "+str(i)+":"+str(hashd)
			lstream.write(frame)
	while True:
		if len(oframes) > 0:
			ndata = oframes.pop(0)
			hashf = hash(ndata)
			if hashf != 0:
				rstream.write(ndata)
		else:
			break

def send_notes():
	while True:
		note = getch()
		if note in 'Qq':
			quit()
		elif note in ['c','d','e','f','g']:
			#print "Playing & Sending " + note
			s.send(note)
			play_note(notes[note])

def stream_audio():
	while True:
		odata = s.recv(CHUNK * CHANNELS * 2)
		oframes.append(odata)
		#ndata = oframes.pop(0)
		#rstream.write(ndata)
		#time.sleep(0.001)

if __name__ == '__main__':

	# Clear screen
	clear = os.system('clear')

	MODE = 'remote'
	PATCH = 'brass'

	WPATH = '.'
	INSTR=WPATH+'/wav/'+PATCH

	c = wave.open(INSTR+'/C.wav', 'r')
	d = wave.open(INSTR+'/D.wav', 'r')
	e = wave.open(INSTR+'/E.wav', 'r')
	f = wave.open(INSTR+'/F.wav', 'r')
	g = wave.open(INSTR+'/G.wav', 'r')

	notes = {'c': c, 'd': d, 'e': e, 'f': f, 'g': g}

	p = pyaudio.PyAudio()

	#for i in range(p.get_device_count()):
	#	print p.get_device_info_by_index(i)

	OID = 1

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

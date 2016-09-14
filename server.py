#A###########################################
# SERVER.PY
############################################
# The server.py is the server component of
# the NetAudio prototype suite. It plays
# the remote instrumentss and streams audio
# back to the local client.
############################################

import os
import sys
import time
import logging
import netmixer
import datetime
import struct
import socket
import numpy as np
from getch import getch, pause
from Queue import Queue
from threading import Thread, currentThread

CHUNK = 64
CHANNELS = 2

logging.basicConfig(
	format='%(asctime)s %(levelname)s %(message)s',
	filename='server_logs.log',
	level=logging.INFO,
	)

logger = logging.getLogger('server')
netmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)

WPATH = os.getcwd()
#WPATH = os.path.dirname(os.path.realpath(__file__))

#INSTR=WPATH+'/wav/piano'
#INSTR=WPATH+'/wav/strings'
#INSTR=WPATH+'/wav/perc'
INSTR=WPATH+'/wav/brass'
#INSTR=WPATH+'/wav/glock'

# Set Sounds
c = netmixer.Sound(INSTR+'/C.wav')
d = netmixer.Sound(INSTR+'/D.wav')
e = netmixer.Sound(INSTR+'/E.wav')
f = netmixer.Sound(INSTR+'/F.wav')
g = netmixer.Sound(INSTR+'/G.wav')

notes = {'c': c, 'd': d, 'e': e, 'f': f, 'g': g}

def runmixer_and_stream():
	while True:
		odata, frame_occur, note, tag = netmixer.tick()
		time.sleep(0.001)
		if frame_occur:         # fetch only sound event
			try:
				if tag:
					#pass
					#print 'before modsend data', len(odata)
					odata = odata+'net{}:{}mixer'.format(note,tag)
					#print 'after modsend data', len(odata)
					print '[TICK] %s with tag #%d at %s'%(note, tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
				conn.send(odata)
			except socket.error, e:
				break
			
if __name__ == "__main__":

	HOST = '0.0.0.0'
	PORT = 12345

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
	s.bind((HOST, PORT))
	s.listen(5)

	global conn
	conn, addr = s.accept()

	Ts = Thread(target = runmixer_and_stream)
	Ts.start()

	# logger.info('Server listening....')

	os.system('clear')
	print "\nServer started..."

	while True:
		unpacker = struct.Struct('si')
		try:
			rcv_note = conn.recv(unpacker.size)
			if len(rcv_note) > 0:
				note, tag = unpacker.unpack(rcv_note)
				if note in ['c','d','e','f','g']:
					print "[RECV] %s with tag #%d at %s"%(note, tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
					notes[note].play(gnote=note, frame_tag=tag)
					#print "Playing " + note + str(tag)

		except socket.error, e:
			break
		
		

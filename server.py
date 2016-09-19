############################################
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
import base64
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
# DEBUG = False
DEBUG = True

logging.basicConfig(
	format='%(asctime)s %(levelname)s %(message)s',
	filename='server_logs.log',
	level=logging.INFO,
	)

logger = logging.getLogger('server')
netmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)
WPATH = os.getcwd()
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
	global stop_stream

	while True:
		odata, frame_occur, note, tag = netmixer.tick()
		time.sleep(0.001)
		if frame_occur:         # fetch only sound event
			try:
				if DEBUG:
					if tag:
						odata = odata+'data----{}:{}----data'.format(note,tag)
						print '[TICK] %s with tag #%d at %s'%(note, tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
				
				encode = base64.b64encode(odata) 		# encode binary buffer to b64
				conn.send(encode)

			except socket.error, e:
				break
			
		if stop_stream:
			break


if __name__ == "__main__":
	stop_stream = False
	try:

		# global conn
		
		HOST = '0.0.0.0'
		PORT = 12345

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  		# occurs because the previous execution of your script has left the socket in a TIME_WAIT state, and can't be immediately reused, This can be resolved by using the socket.SO_REUSEADDR flag.
		s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		s.bind((HOST, PORT))
		s.listen(5)
		conn, addr = s.accept()
			
		Ts = Thread(target = runmixer_and_stream)
		Ts.start()
		os.system('clear')
		
		print "\nServer started...To exit gracefully press ctrl + c" 		# Can we display this also in debug mode ?

		while True:
			unpacker = struct.Struct('si')
			try:
				rcv_note = conn.recv(unpacker.size)
				if len(rcv_note) > 0:
					note, tag = unpacker.unpack(rcv_note)
					if note in ['c','d','e','f','g']:
						
						if DEBUG:
							print "[RECV] %s with tag #%d at %s"%(note, tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
						
						notes[note].play(gnote=note, frame_tag=tag, debug=DEBUG)
						
					elif note == 'q': 		# Here we disconnect client connection from server and send quit signal to client 
						conn.send(note)
						
			except socket.error, e:
				if e.errno in [56,57]: 		# If connection reset (ECONNRESET) or not connected (ENOTCONN) exception occurred
					if DEBUG:
						print 'Server re-initiated'
					conn, addr = s.accept()

	except KeyboardInterrupt:
		if DEBUG:
			print 'Exit from main thread'
		stop_stream = True
		sys.exit(1)

		

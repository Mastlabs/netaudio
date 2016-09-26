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
import cPickle
import logging
import netmixer
import datetime
import struct
import socket
import zlib
import numpy as np
from getch import getch, pause
from Queue import Queue
from threading import Thread, currentThread, enumerate

CHUNK = 64
CHANNELS = 2
DEBUG = False
OFFSET = 0

logging.basicConfig(
	format='%(asctime)s %(levelname)s %(message)s',
	filename='server_logs.log',
	level=logging.INFO,
	)

logger = logging.getLogger('server')
netmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)
netmixer.start()

def load_instruments(patch):
	global notes
	# WPATH = os.getcwd()
	INSTR = 'http://45.79.175.75/{patch}'.format(patch=patch)
	print 'hybrid inst', INSTR
	c = netmixer.Sound(INSTR+'/C.wav')
	d = netmixer.Sound(INSTR+'/D.wav')
	e = netmixer.Sound(INSTR+'/E.wav')
	f = netmixer.Sound(INSTR+'/F.wav')
	g = netmixer.Sound(INSTR+'/G.wav')

	notes = {'c': c, 'd': d, 'e': e, 'f': f, 'g': g}

def runmixer_and_stream(conn):

	global stop_stream

	while True:
		if stop_stream:
			break

		odata, note, tag = netmixer.tick()
		time.sleep(0.001)
		# if odata:
		try:
			if DEBUG:
				if tag:
					# odata = odata+'data----{}:{}----data'.format(note,tag)
					# odata = base64.b64encode(odata) 		# encode binary buffer to b64
					print '[TICK] %s with tag #%d at %s'%(note, tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
				
			conn.send(odata)
		except socket.error, e:
			break

	conn.close()

def run_server(HOST, PORT):

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  		# occurs because the previous execution of your script has left the socket in a TIME_WAIT state, and can't be immediately reused, This can be resolved by using the socket.SO_REUSEADDR flag.
	s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
	s.bind((HOST, PORT))
	s.listen(5)
	conn, addr = s.accept()
		
	# Ts = Thread(target = runmixer_and_stream, args=(conn, ))
	# Ts.start()
	os.system('clear')
	
	print "New Connection from %s:%d"%(addr[0], addr[1])
	print "\nServer started...To exit gracefully press ctrl + c" 		# Can we display this also in debug mode ?

	try:
		cmd = conn.recv(64)
		patch, debug, offset = cPickle.loads(cmd)
		
		load_instruments(patch)

		global DEBUG
		if debug: 		# Auto eval boolean flag
			DEBUG = debug

		global OFFSET
		if offset:
			OFFSET = offset

		if DEBUG:
			print 'check threads in process', enumerate() 		# Here, we used enumerate() function to check whether recursive function creates a new thread or closing old one (we are doing that), if it spawns a new thread this is fatal 

		while True:
			unpacker = struct.Struct('si')
			rcv_note = conn.recv(unpacker.size)
			if len(rcv_note) > 0:
				note, tag = unpacker.unpack(rcv_note)
				if note in ['c','d','e','f','g']:
					print 'play note', note, offset
					if DEBUG:
						print "[RECV] %s with tag #%d at %s"%(note, tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
					
					notes[note].play(
									offset=OFFSET,
									gnote=note, 
									frame_tag=tag, 
									debug=DEBUG,
									socket_conn=conn
								)
				
				elif note == 'q': 		# q key note is only intended for quit purpose only, if used then we raise connection reset error
					raise socket.error(socket.errno.ECONNRESET, 'Connection Reset')

				else:
					if DEBUG:
						print 'Invalid note'
					pass
	
	except socket.error, e:
		if DEBUG:
			print 'error', e
		
		conn.close()
		s.close()
		stop_stream = True

		if e.errno in [socket.errno.ECONNRESET, socket.errno.ENOTCONN]: 		# If connection reset (ECONNRESET) or not connected (ENOTCONN) exception occurred
			if DEBUG:
				print 'Server re-initiated'

			run_server(HOST, PORT) 		# Close old socket object and connection and re-create recursively


if __name__ == "__main__":
	
	stop_stream = False
	# HOST = '0.0.0.0'
	HOST = '127.0.0.1'
	PORT = 12345

	try:
		print 'Waiting...'
		run_server(HOST, PORT)

	except KeyboardInterrupt:
		if DEBUG:
			print 'Exit from main thread'
		stop_stream = True
		sys.exit(1)

	
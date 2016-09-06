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
import logging
import socket
import netmixer
import threading

logging.basicConfig(
	format='%(asctime)s %(levelname)s %(message)s',
	filename='server_logs.log',
	level=logging.INFO,
	)

logger = logging.getLogger('server')

class ThreadedServer(object):
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		self.sock.bind((self.host, self.port))
		netmixer.init(samplerate=44100, chunksize=64, stereo=True) 		 # Channel handling is already implemented in netmixer

		WPATH = os.getcwd()
		#INSTR=WPATH+'/wav/piano'
		#INSTR=WPATH+'/wav/strings'
		#INSTR=WPATH+'/wav/perc'
		INSTR = WPATH+'/wav/brass'
		#INSTR=WPATH+'/wav/glock'

		c = netmixer.Sound(INSTR+'/C.wav')
		d = netmixer.Sound(INSTR+'/D.wav')
		e = netmixer.Sound(INSTR+'/E.wav')
		f = netmixer.Sound(INSTR+'/F.wav')
		g = netmixer.Sound(INSTR+'/G.wav')
		self.notes = {'c': c, 'd': d, 'e': e, 'f': f, 'g': g}

	def runmixer_and_stream(self, client, address):
		while True:
			odata, gtick = netmixer.tick()
			time.sleep(0.001)
			try:
				client.send(odata)
				logger.info("Sending frame data size %s and seq %s"%(len(odata), gtick))
			except socket.error, e:
				break
			
	def listen(self):
		self.sock.listen(10)
		while True:
			try:
				client, address = self.sock.accept() 		# thread per client to avoid the blocking
				client.settimeout(60) 					# If client does not respond within  60 sec
				t1 = threading.Thread(target = self.listenToClient, args = (client, address)).start()
				t2 = threading.Thread(target = self.runmixer_and_stream, args = (client, address)).start()
				t2.join()

			except Exception, e:
				print 'No client remaining to listen'
				break
			
	def listenToClient(self, client, address):
		size = 64
		while True:
			try:
				note = client.recv(size)
				if note:
					if note in self.notes.keys():
						self.notes[note].play()
						print "Playing " + note

			except socket.error, e:
				break


if __name__ == "__main__":
	port_num = 12345
	ThreadedServer('', port_num).listen()


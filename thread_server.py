import os
import sys
import time
import logging
import socket
import threading
import netmixer
import SocketServer

logging.basicConfig(
	format='%(asctime)s %(levelname)s %(message)s',
	filename='server_logs.log',
	level=logging.INFO,
	)

logger = logging.getLogger('server')

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

	def runmixer(self):
		while True:
			odata, gtick = netmixer.tick()
			time.sleep(0.001)
			print 'send data', odata
			try:
				self.request.sendall(odata)
			except Exception, e:
				break

	def setup(self):
		
		WPATH = os.getcwd()
		#INSTR=WPATH+'/wav/piano'
		#INSTR=WPATH+'/wav/strings'
		#INSTR=WPATH+'/wav/perc'
		INSTR = WPATH+'/wav/brass'
		#INSTR=WPATH+'/wav/glock'

		netmixer.init(samplerate=44100, chunksize=64, stereo=True) 		 # Channel handling is already implemented in netmixer
		
		c = netmixer.Sound(INSTR+'/C.wav')
		d = netmixer.Sound(INSTR+'/D.wav')
		e = netmixer.Sound(INSTR+'/E.wav')
		f = netmixer.Sound(INSTR+'/F.wav')
		g = netmixer.Sound(INSTR+'/G.wav')
		self.notes = {'c': c, 'd': d, 'e': e, 'f': f, 'g': g}
		t = threading.Thread(name='mix', target=self.runmixer)
		t.daemon = True
		t.start()
	
	def handle(self):
		try:
			note = self.request.recv(64)
			while note != '': 		# to handle more than one send/recv, loop until recv() returns 0
				cur_thread = threading.current_thread()
				response = "{}: {}".format(cur_thread.name, note)
				print "{} wrote: {}".format(self.client_address[0], response)
			
				if note in self.notes.keys():
					self.notes[note].play()

				note = self.request.recv(64)

		except socket.error, e:
			pass

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass

if __name__ == "__main__":

	HOST, PORT = "0.0.0.0", 6666
	server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
	server_thread = threading.Thread(target=server.serve_forever)
	# Exit the server thread when the main thread terminates
	server_thread.daemon = True
	server_thread.start()
	server_thread.join()
	print "Server loop running in thread:", server_thread.name
	# server.shutdown()
	# server.server_close()


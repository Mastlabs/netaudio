import os
import sys
import socket
import swmixer
import pyaudio
import wave
import time
from swmixer import tick
from getch import getch, pause
from threading import Thread , currentThread  # added thread import -cjh


HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 5000              # Arbitrary non-privileged port
frames = []

swmixer.init(samplerate=44100, chunksize=1024, stereo=True)

def udpStream(CHUNK, CHANNELS):

	udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	udp.bind((HOST, PORT))
	
	print '-'*10
	print 'To quit server unconditionally, press q'

	while True:

		key = getch()
		if key == 'q':
			print 'Server going down'
			break

		print >>sys.stderr, '\nwaiting to receive message'
		
		soundData, addr = udp.recvfrom(CHUNK * CHANNELS * 2)
		
		print >>sys.stderr, 'received %s bytes from %s' % (len(soundData), addr)

		if soundData:
			sent = udp.sendto(soundData, addr)
        	print >>sys.stderr, 'sent %s bytes back to %s' % (sent, addr)

	udp.close()

				
if __name__ == "__main__":
	
	CHUNK = 2048
	CHANNELS = 2	
	udpStream(CHUNK, CHANNELS)

	# Ts = Thread(name='udpstream', target = udpStream, args=(CHUNK,))
	# Ts.setDaemon(True)
	# Ts.start()
	# Ts.join()

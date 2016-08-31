import os
import sys
import time
import logging
import pyaudio
import datetime
import socket
from getch import getch, pause
from threading import Thread, currentThread
from config import swmixer, CHUNK, CHANNELS, WAVE_DIR, r, cPickle

logging.basicConfig(
					format='%(asctime)s %(levelname)s %(message)s',
					filename='server_logs.log',
					level=logging.INFO,
				)

logger = logging.getLogger('server')

c = swmixer.Sound('wav/C.wav')
d = swmixer.Sound('wav/D.wav')
e = swmixer.Sound('wav/E.wav')
f = swmixer.Sound('wav/F.wav')
g = swmixer.Sound('wav/G.wav')

notes = {'c': c, 'd': d, 'e': e, 'f': f, 'g': g}
	
def runmixer_and_stream():
	"""
	The samplerate and chunksize will limit your framerate. If you set the samplerate to 44100 samples per second, 
	and each chunk is 1024 samples, then each call to swmixer.tick() will process 1024 samples corresponding to 
	0.0232 seconds of audio. This will lock your framerate at 1/.0232=43.1 frames per second. If you 
	call swmixer.tick() faster than this, that's OK, it will just block until more audio can be send to 
	the soundcard. If you call swmixer.tick() slower than 43.1 times a second, there will be audio glitches.
	client_addr -> tuple of ip and port

	"""
	
	print currentThread().getName(), 'Start'
	while True:
		
		odata = swmixer.tick()
		time.sleep(0.001)
		
		# DEBUG: USE MIXER HERE IF SOUND DOES NOT HAPPEN ON CLIENT SIDE: swmixer.gstream.write(odata)
		# swmixer.gstream.write(odata)

		if odata != '':
			logger.info('sending %s audio frames'%(len(odata)))
			conn.send(odata)

	print currentThread().getName(), 'Exit'
	conn.close()

if __name__ == "__main__":

	HOST = '0.0.0.0'
	PORT = 12345

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
	s.bind((HOST, PORT))
	s.listen(5)

	conn, addr = s.accept()

	Ts = Thread(target = runmixer_and_stream)
	Ts.start()

	logger.info( 'Server listening....' )
	
	while True:
		rcv_key_event = conn.recv(CHUNK * CHANNELS * 2)
		if rcv_key_event != '':
			snd = notes.get(rcv_key_event, None)
			if snd: snd.play()

			# note_content = r.hget('samples', rcv_key_event.upper() or rcv_key_event.lower())
			# if note_content is not None:
			# 	cPickle.loads(note_content).play()
				

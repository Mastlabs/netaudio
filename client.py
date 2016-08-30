import os
import datetime
import logging
import swmixer
import socket
import sys
import time
from threading import Thread, currentThread
from getch import getch, pause

logging.basicConfig(
					format='%(asctime)s %(levelname)s %(message)s',
					filename='client_logs.log',
                    level=logging.INFO,
				)

logger = logging.getLogger('client')
frames = []

# keyboard takes qwerty input
def record_play_note():
	"""
	play local sample (samples) and streams that audio back out to the local device audio output
	"""

	wave_dir = os.listdir(WAVE_DIR)

	while True:
		
		key = getch()
		wav_file = None

		logger.info('pressed key is: %s'%key)

		if key == 'q':
			break

		if wave_dir:
			for note in wave_dir:
				if (key.upper()+'.wav' or key.lower()+'.wav') == note:
					wav_file = note
					break
					
			if wav_file:
				key_event = wav_file
				s.send(key_event)

		else:
			break
	
	s.close()

def stream_incoming_odata():
	
	while True:
		rcv_key_event_odata = s.recv(CHUNK * CHANNELS * 2)
		if rcv_key_event_odata:
			logger.info('receive audio stream %s'%len(rcv_key_event_odata))
			swmixer.gstream.write(rcv_key_event_odata)

if __name__ == "__main__":

	WAVE_DIR = os.getcwd()+'/wav/'
	CHUNK = 64
	CHANNELS = 2

	# setup socket
	HOST = ''
	PORT = 12345

	# initialize the mixer
	swmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))

	keys = Thread(target=record_play_note)	
	keys.start()
	
	stream = Thread(target=stream_incoming_odata)
	stream.start()
	stream.join()

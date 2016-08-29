import os
import datetime
import logging
import swmixer
import socket
import sys
import time
from threading import Thread, currentThread
from getch import getch, pause

WAVE_DIR = os.getcwd()+'/wav/'

# initialize the mixer
swmixer.init(samplerate=44100, chunksize=64, stereo=True)
swmixer.obuffer = True

# setup socket
HOST = ''
PORT = 12345

logging.basicConfig(
					format='%(asctime)s %(levelname)s %(message)s',
					filename='client_logs.log',
                    level=logging.INFO,
				)

logger = logging.getLogger('client')

# keyboard takes qwerty input
def record_play_note():
	"""
	play local sample (samples) and streams that audio back out to the local device audio output
	"""

	print currentThread().getName(), 'Start'

	wave_dir = os.listdir(WAVE_DIR)

	while True:
		
		key = getch()
		wav_file = None

		print 'pressed key is: ', key

		if key == 'q':
			break

		if wave_dir:
			for note in wave_dir:
				if (key.upper()+'.wav' or key.lower()+'.wav') == note:
					wav_file = note
					break
					
			if wav_file:
				print 'open wave file', WAVE_DIR+wav_file
				snd = swmixer.Sound(WAVE_DIR+wav_file)
				snd.play()

		else:
			break
	
	print currentThread().getName(), 'Exit'


def runmixer_and_stream():
	"""
	The samplerate and chunksize will limit your framerate. If you set the samplerate to 44100 samples per second, 
	and each chunk is 1024 samples, then each call to swmixer.tick() will process 1024 samples corresponding to 
	0.0232 seconds of audio. This will lock your framerate at 1/.0232=43.1 frames per second. If you 
	call swmixer.tick() faster than this, that's OK, it will just block until more audio can be send to 
	the soundcard. If you call swmixer.tick() slower than 43.1 times a second, there will be audio glitches.
	
	DO NOT USE LOGGER (or ANY IO OPS) IN TICK, PUT HERE CAUSE GLITCHES. I AM SORT IT OUT LATER, USE PRINT FOR NOW
	"""

	udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	while True:
		
		data = swmixer.tick()
		print "PLAY TIK FRAMES: " + str(len(data))

		time.sleep(0.001)
		udp.sendto(data, (HOST, PORT))
		
		rcv_data, server = udp.recvfrom(512)  		# 
		if rcv_data:
			swmixer.gstream.write(rcv_data)

if __name__ == "__main__":

	# Start sampler/mixer thread
	mix = Thread(target=runmixer_and_stream)
	keys = Thread(target=record_play_note)
	
	keys.start()
	mix.start()
	mix.join()

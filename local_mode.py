import os
import sys
import swmixer
import time
from getch import getch, pause
from threading import Thread, currentThread

WAVE_DIR = os.getcwd()+'/wav/'
swmixer.init(samplerate=44100, chunksize=1024, stereo=True)
swmixer.start()

print 'press Q to quit'

def keyboard():
	"""
	play local sample (samples) and streams that audio back out to the local device audio output
	"""

	print currentThread().getName(), 'Start'

	while True:
		
		key = getch()
		wav_file = None

		if key == 'Q':
			break

		print 'pressed key is: ', key

		for note in os.listdir(WAVE_DIR):
			if (key.upper()+'.wav' or key.lower()+'.wav') == note:
				wav_file = note
				break	
		
		if wav_file:
			snd = swmixer.Sound(WAVE_DIR+wav_file)
			snd.play()
		
		else:
			print 'bad key pressed'


keys = Thread(name='keyb', target=keyboard)
keys.setDaemon(True)
keys.start()
keys.join()

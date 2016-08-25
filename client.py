import swmixer
import sys
import socket
import time
import wave
import os           # Added os import -cjh
from threading import Thread, currentThread
from getch import getch, pause
from swmixer import tick


HOST = ''
PORT = 12345
buffer, frames = [], []
WAVE_DIR = os.getcwd()+'/wav/'


def swmixtick(tick):
	return

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

		if wave_dir:
			for note in wave_dir:
				if (key.upper()+'.wav' or key.lower()+'.wav') == note:
					wav_file = note
					break
					
			if wav_file:
				print 'open wave file', wav_file

				try:
					wave_note = wave.open(WAVE_DIR + wav_file, 'rb')
				except wave.Error, e: #modified so would compile -cjh
					print e
				
				snd = swmixer.Sound(WAVE_DIR+wav_file)
				snd.play()

		else:
			break
	
	print currentThread().getName(), 'Exit'

	return

def runmixer():

	print currentThread().getName(), 'Start'

	while True:
		swmixer.tick()

	print currentThread().getName(), 'Exit'
	return

def stream():
	""" Read mix buffer and write to output socket"""
	
	print currentThread().getName(), 'Start'
	
	udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	
	while True:
		if len(buffer) > 0:
			val = buffer.pop(0)
			udp.sendto(val, (HOST, PORT))
		else:
			continue

	udp.close()
	
	print currentThread().getName(), 'Exit'

	return


if __name__ == '__main__':

	CHUNK = 64

	play_note = Thread(name='record_buffer', target=record_play_note)
	mixer = Thread(name='mixer', target=runmixer)
	stream = Thread(name='streaming', target=stream)

	play_note.setDaemon(True)
	mixer.setDaemon(True)
	stream.setDaemon(True)

	play_note.start()
	mixer.start()
	stream.start()

	play_note.join()
	mixer.join()
	stream.join()

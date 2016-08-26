import swmixer
import sys
import socket
import time
import wave
import os           # Added os import -cjh
from threading import Thread, currentThread
from getch import getch, pause
from swmixer import tick


buffer, frames = [], []
WAVE_DIR = os.getcwd()+'/wav/'

swmixer.init(samplerate=44100, chunksize=1024, stereo=True)

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
	return

def runmixer():

	print currentThread().getName(), 'Start'
	
	swmixer.obuffer = True
	while True:
		frames.append(swmixer.tick())
		
	print currentThread().getName(), 'Exit'
	return

def stream():
	""" Read mix buffer and write to output socket"""
	
	HOST = ''
	PORT = 5000

	print currentThread().getName(), 'Start'
	udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
	while True:

		if len(frames) > 0:
			print >>sys.stderr, 'sending'
			udp_sock.sendto(frames.pop(0), (HOST, PORT))
		
		else:
			# wait for key press event 
			continue

		print >>sys.stderr, 'waiting to receive'
		
		data, server = udp_sock.recvfrom(4096)
		if data:
			swmixer.gstream.write(data, swmixer.gchunksize)

	udp_sock.close()

	print currentThread().getName(), 'Exit'
	return

if __name__ == '__main__':

	mixer = Thread(name='mixer', target=runmixer)
	play_note = Thread(name='record_buffer', target=record_play_note)
	stream = Thread(name='streaming', target=stream)

	mixer.setDaemon(True)
	play_note.setDaemon(True)
	stream.setDaemon(True)

	mixer.start()
	play_note.start()
	stream.start()

	play_note.join()
	stream.join()

	
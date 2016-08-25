import os
import sys
import socket
import swmixer
import pyaudio
import wave
import time
from swmixer import tick


HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 1234              # Arbitrary non-privileged port

frames = []

def udpStream(CHUNK):

	udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	udp.bind((HOST, PORT))

	while True:
		soundData, addr = udp.recvfrom(CHUNK * CHANNELS * 2)
		frames.append(soundData)
	
	udp.close()
	print 'get data from client', len(frames)

def play(stream, CHUNK):
	while True:
		
		if len(frames) > 0:
			stream.write(frames.pop(0), CHUNK)
		else:
			continue


if __name__ == "__main__":

	FORMAT = pyaudio.paInt16
	CHUNK = 64
	CHANNELS = 2
	RATE = 44100

	p = pyaudio.PyAudio()

	stream = p.open(format=FORMAT,
					channels = CHANNELS,
					rate = RATE,
					output = True,
					frames_per_buffer = CHUNK,
					)

	Ts = Thread(target = udpStream, args=(CHUNK,))
	Tp = Thread(target = play, args=(stream, CHUNK,))
	Ts.setDaemon(True)
	Tp.setDaemon(True)
	Ts.start()
	Tp.start()
	Ts.join()
	Tp.join()

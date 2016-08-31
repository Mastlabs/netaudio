import os
import datetime
import logging
import swmixer
import socket
import sys
import time
from threading import Thread, currentThread
from getch import getch, pause

CHUNK = 64
CHANNELS = 2

# setup socket
HOST = ''
PORT = 12345

logger = logging.getLogger('client')
frames = []

# Logger
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    filename='client_logs.log',
    level=logging.INFO,
    )

# keyboard takes qwerty input
def record_play_note():
    while True:
        note = getch()
        if note == 'q':
            break
        print "Sending note " + note
        s.send(note)
    s.close()

def stream_incoming_odata():
	
	while True:
		rcv_key_event_odata = s.recv(CHUNK * CHANNELS * 2)
		if rcv_key_event_odata:
			#logger.info('receive audio stream %s'%len(rcv_key_event_odata))
			swmixer.gstream.write(rcv_key_event_odata)

if __name__ == "__main__":

	# initialize the mixer
	swmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))

	keys = Thread(target=record_play_note)	
	keys.start()
	
	stream = Thread(target=stream_incoming_odata)
	stream.start()
	stream.join()

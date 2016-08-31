import os
import datetime
import logging
import socket
import sys
import time
from threading import Thread, currentThread
from getch import getch, pause
from config import swmixer, CHANNELS

CHUNK = 64
CHANNELS = 2

logging.basicConfig(
					format='%(asctime)s %(levelname)s %(message)s',
					filename='client_logs.log',
                    level=logging.INFO,
				)

logger = logging.getLogger('client')

def record_play_note():
	"""
	play local sample (samples) and streams that audio back out to the local device audio output
	"""

	logger.info( currentThread().getName() + 'Start' )
	global term

	while True:
		
		key = getch()
		
		logger.info('pressed key is: %s'% key)

		if key == 'q':
			term = True
			break

		s.send(key)

	logger.info( currentThread().getName() + 'Exit' )


def stream_incoming_odata():
	
	while True:
		
		if term == True:
			break

		rcv_key_event_odata = s.recv(CHUNK * CHANNELS * 2)
		if rcv_key_event_odata:
			logger.info( 'receive audio stream of %s'% len(rcv_key_event_odata) )
			swmixer.gstream.write(rcv_key_event_odata)

	s.close()


if __name__ == "__main__":

	HOST = ''
	PORT = 12345

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))
	term = False

	keys = Thread(target=record_play_note)	
	keys.start()
	
	stream = Thread(target=stream_incoming_odata)
	stream.start()
	stream.join()

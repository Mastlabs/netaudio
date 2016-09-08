import socket
import sys
import pyaudio
from getch import getch, pause
from threading import Thread


HOST, PORT = '', 6666
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

p = pyaudio.PyAudio()
pystream = p.open(
			format=pyaudio.paInt16,
			channels=2,
			rate=44100,
			output_device_index=2,
			output=True
		)

def stream_incoming_odata():
	gtick = 0
	while True:
		try:
			odata = sock.recv(64)
			# logger.info("Recv frame data size of %s and seq %s"%(len(odata), gtick))
			pystream.write(odata)

		except Exception, e:
			break

def client():
	
	while True:
		note = getch()
		print 'pressed key is ', note
		if note == 'q':
			break

		sock.send(note)

if __name__ == '__main__':
	t = Thread(name='stream', target=stream_incoming_odata)
	t.daemon = True
	t.start()
	client()
	

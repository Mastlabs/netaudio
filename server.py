import logging
import swmixer
import pyaudio
import time
import datetime
import socket
from getch import getch, pause
from threading import Thread

CHUNK = 128
CHANNELS = 2
HOST = '0.0.0.0'
PORT = 12345

logging.basicConfig(
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='server_logs.log',
                    level=logging.INFO,
                )

logger = logging.getLogger('server')

swmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)

def udpStream():

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((HOST, PORT))

    while True:
        data, addr = udp.recvfrom(CHUNK * CHANNELS * 2)
        print 'recv len of ', len(data)
        #TODO: swmixer.gstream.write(data)       # Enable this step means for debugging, here we can check origin frames order
        
        if data:
            logger.info('stream back %s to clients'%len(data))
            sent = udp.sendto(data, addr)

    udp.close()

def killserver():
    while True:
        key = getch()
        if key == "Q":
            break

if __name__ == "__main__":

    Tq = Thread(target = killserver)
    Tq.start()

    Ts = Thread(target = udpStream)
    Ts.setDaemon(True)
    Ts.start()


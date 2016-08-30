#import swmixer
import pyaudio
import time
import datetime
import socket
from getch import getch, pause
from threading import Thread

CHUNK = 128
CHANNELS = 2
FORMAT = pyaudio.paInt16
RATE = 44100
HOST = ''
PORT = 12345 
LOG = "server.log"
#INDEX = 2   # FOR SOUNDFLOWER2
INDEX = 1

frames = []
buffer = []

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind((HOST, PORT))

p = pyaudio.PyAudio()

stream = p.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                output = True,
                output_device_index = INDEX,
                frames_per_buffer = CHUNK,
                )

log = open(LOG, "a")

def logger(message):
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')
    log.write(str(st) + "|S|" + str(message) + "\n")

def udpStream():

    while True:
        data, addr = udp.recvfrom(CHUNK * CHANNELS * 2)
        time.sleep(0.003)
        #stream.write(data)
        buffer.append(data)
        logger("SOK FRAMES: " + str(len(buffer)))

    udp.close()

def play():
    while True:
        if len(buffer) > 0:
            data = buffer.pop(0)
            stream.write(data)
            logger ("PLA FRAMES: " + str(len(buffer)))
        else:
            continue

def killserver():
    while True:
        key = getch()
        if key == "q":
            break

if __name__ == "__main__":

    Tq = Thread(target = killserver)
    Tq.start()

    Ts = Thread(target = udpStream)
    Ts.setDaemon(True)
    Ts.start()

    time.sleep(0.02)

    Tp = Thread(target = play)
    Tp.setDaemon(True)
    Tp.start()

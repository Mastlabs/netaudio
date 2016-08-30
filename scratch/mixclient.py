import shmixer
import socket
import sys
import time
import datetime
from threading import Thread
from getch import getch, pause

# initialize the mixer
shmixer.init(samplerate=44100, chunksize=128, stereo=True)
shmixer.obuffer = True
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# setup socket

HOST = ''
PORT = 12345
LOG = "client.log"

# Setup Frames

frames = []

# pre-load the samples
c = shmixer.Sound("C.wav")
d = shmixer.Sound("D.wav")
e = shmixer.Sound("E.wav")
f = shmixer.Sound("F.wav")
g = shmixer.Sound("G.wav")
x = shmixer.Sound("file.wav")

log = open(LOG, "a") 

def logger(message):
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    log.write(str(st) + "|C|" + str(message) + "\n")

# keyboard takes qwerty input
def keyboard():
    while True:
        '''
        y = 0
        for i in (c,d,e,f,g):
            i.play()
            print "Note: " + str(y) + " | " + str(i)
            y = y+1
            time.sleep(0.4)
        '''
        key = getch()
        #print "Note: " + key
        if key == 'c':
            c.play()
        elif key == 'd':
            d.play()
        elif key == 'e':
            e.play()
        elif key == 'f':
            f.play()
        elif key == 'g':
            g.play()
        elif key == 'q':
            break
        else:
            print "Wrong Key .."
  
def runmixer():
    while True:
        data = shmixer.tick()
        time.sleep(0.002)
        udp.sendto(data, (HOST, PORT))

def udpStream():
    while True:
        if len(frames) > 0:
            val = frames.pop(0)
            udp.sendto(val, (HOST, PORT))
            logger("UDP FRAMES: " + str(len(frames)))
        else:
            continue

    udp.close()


def playbeat():
    x.play()

if __name__ == "__main__":

    # Start socket
    #sock = Thread(target = udpStream)   
    #sock.setDaemon(True)
    #sock.start()

    # Start sampler/mixer thread
    mix = Thread(target=runmixer)
    mix.setDaemon(True)
    mix.start()

    # Play music in background
    #beat = Thread(target=playbeat)
    #beat.setDaemon(True)
    #beat.start()

    # Start keyboard events
    keys = Thread(target=keyboard)
    keys.start()

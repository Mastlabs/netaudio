import swmixer
import sys
import time
import atexit
from threading import Thread
from getch import getch, pause

swmixer.init(samplerate=44100, chunksize=1024, stereo=True)

c = swmixer.Sound("C.wav")
d = swmixer.Sound("D.wav")
e = swmixer.Sound("E.wav")
f = swmixer.Sound("F.wav")
g = swmixer.Sound("G.wav")

def keyboard():
    while True:
        key = getch()
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
        else:
            print "Wrong Key .."

def runmixer():
    while True:
        swmixer.tick()

def playmusic():
    c.play()
    c.play()
    time.sleep(0.10)
    d.play()
    time.sleep(0.10)
    c.play()

mix = Thread(target=runmixer)
mix.start()

keys = Thread(target=keyboard)
keys.start()

'''
playmusic()
xplay = Thread(target=playmusic)
xplay.setDaemon(True)
xplay.start()
xplay.join()
'''

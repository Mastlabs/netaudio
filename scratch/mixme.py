import swmixer
import sys
import time
import atexit
from threading import Thread
from getch import getch, pause

# initialize the mixer
swmixer.init(samplerate=44100, chunksize=1024, stereo=True)

# pre-load the samples
c = swmixer.Sound("C.wav")
d = swmixer.Sound("D.wav")
e = swmixer.Sound("E.wav")
f = swmixer.Sound("F.wav")
g = swmixer.Sound("G.wav")

# keyboard takes qwerty input
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

# runs mixer in tick mode
def runmixer():
    while True:
        swmixer.tick()

if __name__ == "__main__":

    # Start sampler/mixer thread
    mix = Thread(target=runmixer)
    mix.start()

    # Start keyboard events
    keys = Thread(target=keyboard)
    keys.start()

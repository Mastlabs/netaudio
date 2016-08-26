import shmixer
import sys
import time
from threading import Thread
from getch import getch, pause

# initialize the mixer
shmixer.obuffer = False
shmixer.init(samplerate=44100, chunksize=1024, stereo=True)

# Setup Frames

frames = []

# pre-load the samples
c = shmixer.Sound("C.wav")
d = shmixer.Sound("D.wav")
e = shmixer.Sound("E.wav")
f = shmixer.Sound("F.wav")
g = shmixer.Sound("G.wav")

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
        elif key == 'Q':
            break
        else:
            print "Wrong Key .."

# runs mixer in tick mode
def runmixer():
    shmixer.obuffer = True
    while True:
        frames.append(shmixer.tick())
        shmixer.gstream.write(frames.pop(0), shmixer.gchunksize)

if __name__ == "__main__":

    # Start sampler/mixer thread
    mix = Thread(target=runmixer)
    mix.setDaemon(True)
    mix.start()

    # Start keyboard events
    keys = Thread(target=keyboard)
    keys.setDaemon(True)
    keys.start()
    keys.join()

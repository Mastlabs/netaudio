import os
import cPickle
import redis
import time
import swmixer

r = redis.StrictRedis(host='localhost')

CHUNK = 62
CHANNELS = 1
WAVE_DIR = os.getcwd()+'/wav/'

"""

output_device_index values

HDA Intel PCH: ALC662 rev1 Analog (hw:0,0) - 0 (sys specific)
HDA Intel PCH: ALC662 rev1 Alt Analog (hw:0,2) - 1 (sys specific)
sysdefault - 2
pulse - 3
default - 4

"""

swmixer.init(samplerate=44100, chunksize=CHUNK, stereo=True)
swmixer.obuffer = True

if r.hkeys('samples'):
	pass
else:
	for note in os.listdir(WAVE_DIR):
		snd = swmixer.Sound(WAVE_DIR+note)
		r.hset('samples', note.split('.')[0], cPickle.dumps(snd))

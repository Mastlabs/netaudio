import os
import sys
import time
import pyaudio
import wave

CHUNK = 1024

wf = wave.open(sys.argv[1], 'rb')
p = pyaudio.PyAudio()

stream = p.open(
				format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
				rate=wf.getframerate(),
				output=True
			)

print 'input latency ', stream.get_input_latency()

data = wf.readframes(CHUNK)

while data != '':
	stream.write(data)  		# Local play accomplished by buffer audio wav file
	data = wf.readframes(CHUNK)

print 'output latency ', stream.get_output_latency()

stream.stop_stream()
stream.close()	 # close pyaudio connex
wf.close()
p.terminate()

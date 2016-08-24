# NETAUDIO.

**NetAudio** is a remote cloud sampler capable of playing polyphonic digital 
instruments across a network on the behalf of local clients/plugins with
zero latency and full stereo audio fidelity.

Local **clients** launch, connect to the cloud via an upstream control(midi)
socket and a downstream audio (buffer stream) socket.

Local **users** select modes and instruments via the client, press keys and 
hear locally the results of the cloud sampler playing the instruments.

The **cloud** sampler is a multi-threaded server capable of selecting and reading
in various digital instruments (and their corresponding wav files), receiving
control data (midi, key press, etc) and reading in, buffering and streaming
the summed/mixed instrument audio back down to the client in real time.

The **server** prototype may recieve up to 5 concurrent clients, each selecting
and playing an octave of one instrument (8 wav files) in an up to 32-thread
(polyphonic) mode for each client.

There are three modes to the operation: local, remote and hybrid.

**Local:** local client chooses and instrument, captures local  key events 
and plays the local sample instrument files/audio out local system audio

**Remote:** local client selects and instrument, captures local  key events 
to play remote cloud sample instruments, stream audio back down to client 
for local audio output. Network lateny is expected from key event to audio.

**Hybrid:** local client key events are forked both locally and remotely (cloud).
This mode requires an offset value to cover latency of the network round trip.
The offset value determines how long the locally forked control data plays
the local sample "start" - up to the latency offset amount, and from where
the remote samples start (offset) in the array when played back down the
stream to the client. At the client, a triple ring buffer merges the mix of
the local start samples, the incoming remote samples, and seamlessly knits
them into a continuous and unbroken local audio playback of both locally and
remotely "played" samples, with zero latency from the initial local key event.

##Requirments:##
	`pip install -r requirements.txt`


##Components:##

client.py
server.py
wav/<files>

##Usage:##

**Server:** `python server.py`
**Config:** CHUNK SIZE, BUFFER_SIZE, INSTRUMENT, OFFSET, MODE

**Client:** `python client.py`
**Config:** CHUNK SIZE, BUFFER_SIZE, INSTRUMENT, OFFSET, MODE 

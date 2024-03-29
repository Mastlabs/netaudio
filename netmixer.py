"""
NetMixer Realtime Software Mixer
Copyright 2016, Christian Hessler
    
"""

import time
import datetime
import wave
import thread
import numpy
import struct
import urllib2
import base64


ginit = False
gstereo = True
gchunksize = 1024
gsamplerate = 44100
gchannels = 1
gsamplewidth = 2
gmixer_srcs = []
gid = 1
glock = thread.allocate_lock()
gtick = None
note = None
tag = None
s_conn = None

class _SoundSourceData:
    def __init__(self, data, loops):
        self.data = data
        self.pos = 0
        self.loops = loops
        self.done = False
    def set_position(self, pos):
        self.pos = pos % len(self.data)
    def get_samples(self, sz):
        z = self.data[self.pos:self.pos + sz]
        self.pos += sz
        if len(z) < sz:
            # oops, sample data didn't cover buffer
            if self.loops != 0:
                # loop around
                self.loops -= 1
                self.pos = sz - len(z)
                z = numpy.append(z, self.data[:sz - len(z)])
            else:
                # nothing to loop, just append zeroes
                z = numpy.append(z, numpy.zeros(sz - len(z), numpy.int16))
                # and stop the sample, it's done
                self.done = True
        if self.pos == len(self.data):
            # this case loops without needing any appending
            if self.loops != 0:
                self.loops -= 1
                self.pos = 0
            else:
                self.done = True
        return z

class _SoundSourceStream:
    def __init__(self, fileobj, loops):
        self.fileobj = fileobj
        self.pos = 0
        self.loops = loops
        self.done = False
        self.buf = ''
    def set_position(self, pos):
        self.pos = pos
        self.fileobj.seek_time(pos * 1000 / gsamplerate / 2)
    def get_samples(self, sz):
        szb = sz * 2
        while len(self.buf) < szb:
            s = self.fileobj.read()
            if s is None or s == '': break
            self.buf += s[:]
        z = numpy.fromstring(self.buf[:szb], dtype=numpy.int16)
        if len(z) < sz:
            # In this case we ran out of stream data
            # append zeros (don't try to be sample accurate for streams)
            z = numpy.append(z, numpy.zeros(sz - len(z), numpy.int16))
            if self.loops != 0:
                self.loops -= 1
                self.pos = 0
                self.fileobj.seek_time(0)
                self.buf = ''
            else:
                self.done = True
        else:
            # remove head of buffer
            self.buf = self.buf[szb:]
        return z

# A channel is a "sound event" that is playing
class Channel:
    """Represents one sound source currently playing"""
    def __init__(self, src, env):
        global gid
        self.id = gid
        gid += 1
        self.src = src
        self.env = env
        self.active = True
        self.done = False
    def stop(self):
        """Stop the sound playing"""
        glock.acquire()
        # If the sound has already ended, don't raise exception
        try:
            gmixer_srcs.remove(self)
        except ValueError:
            None
        glock.release()
    def pause(self):
        """Pause the sound temporarily"""
        glock.acquire()
        self.active = False
        glock.release()
    def unpause(self):
        """Unpause a previously paused sound"""
        glock.acquire()
        self.active = True
        glock.release()
    def set_volume(self, v, fadetime=0):
        """Set the volume of the sound

        Removes any previously set envelope information.  Also
        overrides any pending fadeins or fadeouts.

        """
        glock.acquire()
        if fadetime == 0:
            self.env = [[0, v]]
        else:
            curv = calc_vol(self.src.pos, self.env)
            self.env = [[self.src.pos, curv], [self.src.pos + fadetime, v]]
        glock.release()
    def get_volume(self):
        """Return current volume of sound"""
        glock.acquire()
        v = calc_vol(self.src.pos, self.env)
        glock.release()
        return v
    def get_position(self):
        """Return current position of sound in samples"""
        glock.acquire()
        p = self.src.pos
        glock.release()
        return p
    def set_position(self, p):
        """Set current position of sound in samples"""
        glock.acquire()
        self.src.set_position(p)
        glock.release()
    def fadeout(self, time):
        """Schedule a fadeout of this sound in given time"""
        glock.acquire()
        self.set_volume(0.0, fadetime=time)
        glock.release()
    def _get_samples(self, sz):
        print 'server audio pos',self.src.pos
        if not self.active: return None
        v = calc_vol(self.src.pos, self.env)
        z = self.src.get_samples(sz)
        if self.src.done: self.done = True
        return z * v



def resample(smp, scale=1.0):
    """Resample a sound to be a different length

    Sample must be mono.  May take some time for longer sounds
    sampled at 44100 Hz.

    Keyword arguments:
    scale - scale factor for length of sound (2.0 means double length)

    """
    # f*ing cool, numpy can do this with one command
    # calculate new length of sample
    n = round(len(smp) * scale)
    # use linear interpolation
    # endpoint keyword means than linspace doesn't go all the way to 1.0
    # If it did, there are some off-by-one errors
    # e.g. scale=2.0, [1,2,3] should go to [1,1.5,2,2.5,3,3]
    # but with endpoint=True, we get [1,1.4,1.8,2.2,2.6,3]
    # Both are OK, but since resampling will often involve
    # exact ratios (i.e. for 44100 to 22050 or vice versa)
    # using endpoint=False gets less noise in the resampled sound
    return numpy.interp(
        numpy.linspace(0.0, 1.0, n, endpoint=False), # where to interpret
        numpy.linspace(0.0, 1.0, len(smp), endpoint=False), # known positions
        smp, # known data points
        )

def interleave(left, right):
    """Given two separate arrays, return a new interleaved array

    This function is useful for converting separate left/right audio
    streams into one stereo audio stream.  Input arrays and returned
    array are Numpy arrays.

    See also: uninterleave()

    """
    return numpy.ravel(numpy.vstack((left, right)), order='F')

def uninterleave(data):
    """Given a stereo array, return separate left and right streams

    This function converts one array representing interleaved left and
    right audio streams into separate left and right arrays.  The return
    value is a list of length two.  Input array and output arrays are all
    Numpy arrays.

    See also: interleave()

    """
    return data.reshape(2, len(data)/2, order='FORTRAN')

def stereo_to_mono(left, right):
    """Return mono array from left and right sound stream arrays"""
    return (0.5 * left + 0.5 * right).astype(numpy.int16)


class Sound:
    """Represents a playable sound"""

    def __init__(self, filename=None, data=None):
        """Create new sound from a WAV file, MP3 file, or explicit sample data"""
        assert(ginit == True)
        # Three ways to construct Sound
        # First is by passing data directly
        if data is not None:
            self.data = data
            return
        if filename is None:
            assert False
        # Second is through a file
        self.data = None
        # Load data from file into self.data
        # Here's how to do it for WAV
        # (Both of the loaders set nc to channels and fr to framerate
        if filename[-3:] in ['wav','WAV']:
            wf = wave.open(filename, 'rb')
            # wf = wave.open(urllib2.urlopen(filename), 'rb')
            #assert(wf.getsampwidth() == 2)
            nc = wf.getnchannels()
            self.framerate = wf.getframerate()
            fr = wf.getframerate()
            # read data
            data = []
            r = ' '
            while r != '':
                r = wf.readframes(4096)
                data.append(r)
            if wf.getsampwidth() == 2:
                self.data = numpy.fromstring(''.join(data), 
                                             dtype=numpy.int16)
            if wf.getsampwidth() == 4: 
                self.data = numpy.fromstring(''.join(data), 
                                             dtype=numpy.int32)
                self.data = self.data / 65536.0
            if wf.getsampwidth() == 1:
                self.data = numpy.fromstring(''.join(data), 
                                             dtype=numpy.uint8)
                self.data = self.data * 256.0
            wf.close()

        if self.data is None:
            assert False
        # Resample if needed
        if fr != gsamplerate:
            scale = gsamplerate * 1.0 / fr
            if nc == 1:
                self.data = resample(self.data, scale)
            if nc == 2:
                # for stereo resample independently
                left, right = uninterleave(self.data)
                nleft = resample(left, scale)
                nright = resample(right, scale)
                self.data = interleave(nleft, nright)
        # Stereo convert if necessary
        if nc != gchannels:
            # oops, stereo-ness differs
            # convert to match init parameters
            if nc == 1:
                # came in mono, need stereo
                self.data = interleave(self.data, self.data)
            if nc == 2:
                # came in stereo, need mono
                # first make it a 2d array
                left, right = uninterleave(self.data)
                self.data = stereo_to_mono(left, right)
        return

    def get_length(self):
        """Return the length of the sound in samples

        To convert to seconds, divide by the samplerate and then divide
        by 2 if in stereo.

        """
        return len(self.data)

    def play(self, 
            volume=1.0, 
            offset=0, 
            fadein=0,
            envelope=None, 
            loops=0, 
            gnote=None, 
            frame_tag=None, 
            debug=False,
            socket_conn=None):

        """Play the sound

        Keyword arguments:
        volume - volume to play sound at
        offset - sample to start playback
        fadein - number of samples to slowly fade in volume
        envelope - a list of [offset, volume] pairs defining
                   a linear volume envelope
        loops - how many times to play the sound (-1 is infinite)
        gnote - the note played
        tag - the note sequence ID

        """
        global note
        global tag
        global gtick
        global s_conn
        sz = gchunksize*gchannels
        gtick = 0
        if gnote:
            note = gnote
            tag = frame_tag
            s_conn = socket_conn        # changed on every play
            if debug:
                print "MIXX PLAY %s with tag #%d at %s"%(note, tag, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))

        if envelope != None:
            env = envelope
        else:
            if volume == 1.0 and fadein == 0:
                env = []
            else:
                if fadein == 0:
                    env = [[0, volume]]
                else:
                    env = [[offset, 0.0], [offset + fadein, volume]]
        src = _SoundSourceData(self.data, loops)
        src.pos = offset * sz if offset > 0 else offset
        sndevent = Channel(src, env)
        glock.acquire()
        gmixer_srcs.append(sndevent)
        glock.release()
        return sndevent

    def scale(self, vol):
        """Scale a sound sample

        vol is 0.0 to 1.0, amount to scale by
        """
        self.data = (self.data * vol).astype(numpy.int16)

    def resample(self, scale):
         """Resample a sound

         scale = 1.0 means original sound
         scale = 0.5 is half as long (up an octave)
         scale = 2.0 is twice as long (down an octave)
         
         """
         self.data = resample(self.data, scale)

class _Stream:
    pass

def _create_stream(filename, checks):
    if filename[-3:] in ['wav','WAV']:
        wf = wave.open(filename, 'rb')
        if checks:
            assert(wf.getsampwidth() == 2)
            assert(wf.getnchannels() == gchannels)
            assert(wf.getframerate() == gsamplerate)
        # create stream object
        stream = _Stream()
        def str_read():
            return wf.readframes(4096)
        # give the stream object a read() method
        stream.read = str_read
        def str_seek_time(t):
            if t == 0: wf.rewind()
            assert(False) # unsupported for WAV streams
        stream.seek_time = str_seek_time
        return stream

class StreamingSound:
    """Represents a playable sound stream"""

    def __init__(self, filename, checks=True):
        """Create new streaming sound from a WAV file or an MP3 file

        The new streaming sound must match the output samplerate
        and stereo-ness.  You can turn off these checks by setting
        the keyword checks=False, but the sound will be distorted.
        
        """
        assert(ginit == True)
        if filename is None:
            assert False
        self.filename = filename
        self.checks = checks

    def get_length(self):
        """Return the length of the sound stream in samples

        Only available for MP3 streams, not WAV ones.  To convert
        result to seconds, divide by the samplerate and then divide by
        2.

        """
        stream = _create_stream(self.filename, self.checks)
        t = stream.total_time() * gsamplerate * 2 / 1000
        del(stream)
        return t

    def play(self, volume=1.0, offset=0, fadein=0, envelope=None, loops=0):
        """Play the sound stream

        Keyword arguments:
        volume - volume to play sound at
        offset - sample to start playback
        fadein - number of samples to slowly fade in volume
        envelope - a list of [offset, volume] pairs defining
                   a linear volume envelope
        loops - how many times to play the sound (-1 is infinite)

        """
        stream = _create_stream(self.filename, self.checks)

        if envelope != None:
            env = envelope
        else:
            if volume == 1.0 and fadein == 0:
                env = []
            else:
                if fadein == 0:
                    env = [[0, volume]]
                else:
                    env = [[offset, 0.0], [offset + fadein, volume]]
        src = _SoundSourceStream(stream, loops)
        src.pos = offset
        sndevent = Channel(src, env)
        glock.acquire()
        gmixer_srcs.append(sndevent)
        glock.release()
        return sndevent

def calc_vol(t, env):
    """Calculate volume at time t given envelope env

    envelope is a list of [time, volume] points
    time is measured in samples
    envelope should be sorted by time

    """
    #Find location of last envelope point before t
    if len(env) == 0: return 1.0
    if len(env) == 1:
        return env[0][1]
    n = 0
    while n < len(env) and env[n][0] < t:
        n += 1
    if n == 0:
        # in this case first point is already too far
        # envelope hasn't started, just use first volume
        return env[0][1]
    if n == len(env):
        # in this case, all points are before, envelope is over
        # use last volume
        return env[-1][1]
        
    # now n holds point that is later than t
    # n - 1 is point before t
    f = float(t - env[n - 1][0]) / (env[n][0] - env[n - 1][0])
    # f is 0.0--1.0, is how far along line t has moved from
    #  point n - 1 to point n
    # volume is linear interpolation between points
    return env[n - 1][1] * (1.0 - f) + env[n][1] * f

def tick():
    """Main loop of mixer, mix and do audio IO

    Audio sources are mixed by addition and then clipped.  Too many
    loud sources will cause distortion.

    """
    global ginit
    global gmixer_srcs
    global gtick
    c = None
    frame_occur = False         # If false: blank noise (0 numpy ndarray) occurred else frame happen on every tick call
    rmlist = []
    if not ginit:
        return
    sz = gchunksize * gchannels
    b = numpy.zeros(sz, numpy.float)
    if glock is None: return # this can happen if main thread quit first
    glock.acquire()
    for sndevt in gmixer_srcs:
        s = sndevt._get_samples(sz)
        if s is not None:
            b += s
            frame_occur = True
            gtick += 1
            if gtick == 1:
                c = tag
                # print 'init frame tag %s'%tag
        if sndevt.done:
            rmlist.append(sndevt)
    b = b.clip(-32767.0, 32767.0)
    for e in rmlist:
        gmixer_srcs.remove(e)

    glock.release()
    if frame_occur:
        odata = (b.astype(numpy.int16)).tostring()
        s_conn.send(odata)

def init(samplerate=44100, chunksize=1024, stereo=True):
    """Initialize mixer

    Must be called before any sounds can be played or loaded.

    Keyword arguments:
    samplerate - samplerate to use for playback (default 22050)
    chunksize - size of playback chunks
      smaller is more responsive but perhaps stutters
      larger is more buffered, less stuttery but less responsive
      Can be any size, does not need to be a power of two. (default 1024)
    stereo - whether to play back in stereo
    """
    
    global gstereo, gchunksize, gsamplerate, gchannels, gsamplewidth
    global ginit
    assert (10000 < samplerate <= 48000)
    gsamplerate = samplerate
    gchunksize = chunksize
    assert (stereo in [True, False])
    gstereo = stereo
    if stereo:
        gchannels = 2
    else:
        gchannels = 1
    gsamplewidth = 2
    ginit = True

def start():
    """Start separate mixing thread"""
    global gthread
    def f():
        while True:
            try:
                tick()
                time.sleep(0.001)
            except Exception, e:
                pass
    gthread = thread.start_new_thread(f, ())

def quit():
    """Stop all playback and terminate mixer"""
    global ginit
    glock.acquire()
    ginit = False
    glock.release()

def set_chunksize(size=1024):
    """Set the audio chunk size for each frame of audio output

    This function is useful for setting the framerate when audio output
    is synchronized with video.
    """
    global gchunksize
    glock.acquire()
    gchunksize = size
    glock.release()

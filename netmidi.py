##########################################
# MIDI.PY
##########################################
#
# This module allows you to select your
# MIDI instrument and capture/stream
# the MIDI data to the client or server.  
#
##########################################

import pygame
import pygame.midi
import time
import datetime
from pygame.locals import *
import os

# INITIALIZE
pygame.init()
pygame.midi.init()
pygame.fastevent.init()
event_get = pygame.fastevent.get
event_post = pygame.fastevent.post
midi_count = pygame.midi.get_count()
input_id = 0
hline = "--------------------------------------"
instruments = {'0':'strings', 
                '1':'brass',
                '2':'piano',
                '3':'perc',
                '4':'glock'
                }

# ------------------------------
# select_midi_device()
#   returns midi_device_id (int)
# ------------------------------

def select_midi_device():
    os.system('clear')
    print hline
    print "MIDI DEVICES"
    print hline

    for id in range(midi_count):
        mface, mname, minput, moutput, mopened = pygame.midi.get_device_info(id)
        print "["+str(id)+"] " +  str(mname)

    print hline
    choice = raw_input("Choose your MIDI device [#] ")
    in_id = choice
    time.sleep(1)

    return int(in_id)


#------------------------------
# select_instrument()
#------------------------------

def select_instrument():

    os.system('clear')

    print hline
    print "CHOOSE INSTRUMENT:"
    print hline

    #print instruments.keys()
    #print instruments.values()
    keylist = instruments.keys()
    for key in range (len(keylist)):
        print "["+str(key)+"] " + instruments[str(key)]

    choice = raw_input("Choose your Instrument [#] ")
    patch = instruments[choice] 
    time.sleep(1)
    return patch

# ------------------------------
# select_mode()
# ------------------------------

def select_mode():
    modes = {'1':'local', '2':'remote', '3':'hybrid', 'Q':'quit'}
    os.system('clear')

    print hline
    print "SELECT MODE"
    print hline

    print "[1] LOCAL"
    print "[2] REMOTE"
    print "[3] HYBRID"
    print "-----------"
    print "[Q] QUIT"
    print hline

    key = raw_input("\nSelect your mode[#]: ")
    return modes[str(key)]


# ------------------------------
# capture_midi()
# ------------------------------

def capture_midi(input_id):

    i = pygame.midi.Input( input_id )
    os.system('clear')

    print hline
    print "Starting MIDI stream ..."
    print hline

    going = True

    while going:

        if i.poll():
            midi_events = i.read(10)
            #print midi_events
            if midi_events[0][0][2] > 0:
                note = midi_events[0][0][1]
                print note

    i.close()

###################################

if __name__ == '__main__':

    while True:
        mode = select_mode()
        if mode in ('Q', 'q'):
            break
        input_id = select_midi_device()
        instrument_id = select_instrument()
        capture_midi(input_id)

    os.system('clear')
    print hline
    print "SHUTTING DOWN"
    print hline
    time.sleep(1)

    pygame.midi.quit()
    pygame.quit()
    exit()

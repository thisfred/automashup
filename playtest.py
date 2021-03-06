#!/usr/bin/env python
"""Play a wave file."""
import alsaaudio
import sys

card = 'default'

# Open the device in playback mode.
out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, card=card)

# Set attributes: Mono, 44100 Hz, 16 bit little endian frames
out.setchannels(1)
out.setrate(44100)
out.setformat(alsaaudio.PCM_FORMAT_S16_LE)

# The period size controls the internal number of frames per period.
# The significance of this parameter is documented in the ALSA api.
out.setperiodsize(160)

f=open("/usr/lib/libreoffice/share/gallery/sounds/soft.wav",'rb')
f2=open("/usr/lib/libreoffice/share/gallery/sounds/soft.wav",'rb')
# Read data from stdin
data = f.read(320)
data2 = f.read(320)
while data:
    out.write(data)
    data = f.read(320)
while data2:
    out.write(data2)
    data2 = f2.read(320)
            

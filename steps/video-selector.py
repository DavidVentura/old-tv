#!/usr/bin/env python3
import gi
import time
gi.require_version('Gst', '1.0')
from gi.repository import Gst

Gst.init(None)

sources = [ 'tcpclientsrc host=192.168.1.7 port=2000 ! queue ! matroskademux name=d1 ! queue ! avdec_h264',
            'tcpclientsrc host=192.168.1.7 port=4000 ! queue ! matroskademux name=d2 ! queue ! avdec_h264',
            'tcpclientsrc host=192.168.1.7 port=5000 ! queue ! matroskademux name=d3 ! queue ! avdec_h264',
            'tcpclientsrc host=192.168.1.7 port=8000 ! queue ! matroskademux name=d4 ! queue ! avdec_h264',
          ]

v_output = 'videoconvert !  autovideosink'
s_sources = ' ! in. '.join(sources)
s =  '{sources} ! in. input-selector name=in ! {output}'.format(output=v_output, sources=s_sources)

asources = [
            'd1. ! queue ! mpegaudioparse ! avdec_mp3',
            'd2. ! queue ! mpegaudioparse ! avdec_mp3',
            'd3. ! queue ! mpegaudioparse ! avdec_mp3',
            'd4. ! queue ! mpegaudioparse ! avdec_mp3',
        ]
a_output = 'audioconvert ! autoaudiosink'
a_sources = ' ! ain. '.join(asources)
s = '{s} {asources} ! ain. input-selector name=ain ! {output}'.format(asources=a_sources, s=s, output=a_output)
print(s)
pipeline = Gst.parse_launch(s)

pipeline.set_state(Gst.State.PLAYING)
idx = 0


def do_switch(idx):
    idx = max(idx, 0)
    idx = min(idx, len(sources))
    newpad = aswitch.get_static_pad('sink_%d' % idx)
    aswitch.set_property("active-pad", newpad)

    newpad = vswitch.get_static_pad('sink_%d' % idx)
    vswitch.set_property("active-pad", newpad)
    print("Switched to %d" % idx)


vswitch = pipeline.get_by_name('in')
aswitch = pipeline.get_by_name('ain')
do_switch(0)
while True:
    print("Waiting for input")
    i = input()
    try:
        idx = int(i)
    except:
        print("Invalid input")
        continue

    do_switch(idx)

pipeline.set_state(Gst.State.NULL)

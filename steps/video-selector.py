#!/usr/bin/env python3
import gi
import time
gi.require_version('Gst', '1.0')
from gi.repository import Gst

Gst.init(None)

sources = [ 'tcpclientsrc host=192.168.1.7 port=2000 ! queue ! matroskademux name=d1 ! queue ! h264parse',
            'tcpclientsrc host=192.168.1.7 port=4000 ! queue ! matroskademux name=d2 ! queue ! h264parse',
            'tcpclientsrc host=192.168.1.7 port=5000 ! queue ! matroskademux name=d3 ! queue ! h264parse',
            'tcpclientsrc host=192.168.1.7 port=8000 ! queue ! matroskademux name=d4 ! queue ! h264parse',
          ]

v_output = 'm.'
s_sources = ' ! in. '.join(sources)
s =  '{sources} ! in. input-selector name=in ! {output}'.format(output=v_output, sources=s_sources)

asources = [
            'd1. ! queue',
            'd2. ! queue',
            'd3. ! queue',
            'd4. ! queue',
        ]
a_output = 'matroskamux streamable=true name=m'
a_sources = ' ! ain. '.join(asources)
s = '{s} {asources} ! ain. input-selector name=ain ! mpegaudioparse ! {output}'.format(asources=a_sources, s=s, output=a_output)

s = s + ' ! tcpserversink host=0.0.0.0 port=4444 sync-method=next-keyframe'
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

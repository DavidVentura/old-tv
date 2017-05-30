#!/bin/bash
DURATION=60
FRAMERATE=30
DURATION=6
gst-launch-1.0 videotestsrc pattern=snow num-buffers=$((DURATION*FRAMERATE)) ! video/x-raw,width=576,height=432,framerate=$FRAMERATE/1 ! progressreport ! x264enc psy-tune=grain qp-max=30 key-int-max=15 ! video/x-h264,profile=high ! h264parse ! mp4mux name=m ! filesink location=test.mp4 audiotestsrc wave=pink-noise num-buffers=$DURATION samplesperbuffer=44100 volume=0.1 ! audio/x-raw,channels=1,rate=44100 ! lamemp3enc ! m.

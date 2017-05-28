#!/bin/bash

gst-launch-1.0 -qe filesrc location=fast2.mp4 ! qtdemux name=d ! queue ! mpegaudioparse ! m. d. ! queue ! h264parse ! matroskamux name=m streamable=true ! tcpserversink host=0.0.0.0 port=2000 sync-method=latest-keyframe &
gst-launch-1.0 -qe filesrc location=fast4.mp4 ! qtdemux name=d ! queue ! mpegaudioparse ! m. d. ! queue ! h264parse ! matroskamux name=m streamable=true ! tcpserversink host=0.0.0.0 port=4000 sync-method=latest-keyframe &
gst-launch-1.0 -qe filesrc location=fast5.mp4 ! qtdemux name=d ! queue ! mpegaudioparse ! m. d. ! queue ! h264parse ! matroskamux name=m streamable=true ! tcpserversink host=0.0.0.0 port=5000 sync-method=latest-keyframe &
gst-launch-1.0 -qe filesrc location=fast8.mp4 ! qtdemux name=d ! queue ! mpegaudioparse ! m. d. ! queue ! h264parse ! matroskamux name=m streamable=true ! tcpserversink host=0.0.0.0 port=8000 sync-method=latest-keyframe &

wait

#!/bin/bash
rm -f noise.mp4
timeout -s int 5 \
	gst-launch-1.0 -e videotestsrc is-live=true pattern=snow !\
	video/x-raw,width=576,height=432,framerate=25/1 !\
	x264enc psy-tune=grain qp-max=30 ! qtmux name=q !\
	filesink location=noise.mp4\
	audiotestsrc wave=white-noise volume=0.02 is-live=true ! voaacenc ! q.


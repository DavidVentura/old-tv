import argparse
import sys
import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst


def bus_call(bus, msg, *args):
    """
    handling messages on the gstreamer bus
    """
    global prerolled, pipeline, loop

    if msg.type == Gst.MessageType.ASYNC_DONE:
        if not prerolled:
            print("Initial seek ...");
            flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT
            pipeline.seek_simple (Gst.Format.TIME, flags, 0);
            prerolled = True
    elif msg.type == Gst.MessageType.SEGMENT_DONE:
        print("Looping...")
        flags = Gst.SeekFlags.SEGMENT
        pipeline.seek_simple (Gst.Format.TIME, flags, 0);
    elif msg.type == Gst.MessageType.ERROR:
        print(msg.parse_error())
        loop.quit()            # quit.... (better restart app?)
    return True


parser = argparse.ArgumentParser(description='Loop a videofile seamlessly.')
parser.add_argument('file', type=str, help='file to play')
args = parser.parse_args()
if not os.path.isfile(args.file):
    print("File {0} doesn't exist".format(args.file))
    sys.exit(1)

Gst.init(None)
GObject.threads_init()
loop = GObject.MainLoop()

# create pipeline pipeline
prerolled = False
pipeline = Gst.parse_launch("filesrc name=file ! qtdemux ! h264parse ! avdec_h264 ! autovideosink")
bus = pipeline.get_bus()
bus.add_watch(0, bus_call, loop) # 0 == GLib.PRIORITY_DEFAULT 

# set properties of elements
src = pipeline.get_by_name("file")
src.set_property("location", os.path.abspath(args.file))

pipeline.set_state(Gst.State.PLAYING)

try:
    loop.run()
except Exception as e:
    print(e)
finally:
    pipeline.set_state(Gst.State.NULL)

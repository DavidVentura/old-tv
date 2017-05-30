#!/usr/bin/env python3
import gi
import sys
import platform
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib

GObject.threads_init()
Gst.init(None)

class Player:

    def msg(self, bus, message):
        if not message:
            return

        t = message.type
        if t != Gst.MessageType.STATE_CHANGED and t != Gst.MessageType.TAG:
            # print(t)
            pass

        if t == Gst.MessageType.EOS:
            print("We got EOS on the pipeline.")
            sys.exit(1)
        elif t == Gst.MessageType.ERROR:
            err, dbg = message.parse_error()
            print("ERROR:", message.src.get_name(), " ", err.message)
            if dbg:
                print("debugging info:", dbg)
        else:
            print("Unexpected message:", t)

    def __init__(self):
        self.mainloop = GObject.MainLoop()
        self.pipeline = Gst.Pipeline.new("mypipeline")
        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message", self.msg)

        f = Gst.ElementFactory.make('filesrc')
        f.set_property('location', "/home/david/git/old-tv/noise/test.mp4")
        q = Gst.ElementFactory.make('qtdemux', 'demuxer_%d' % 0)
        self.p = Gst.ElementFactory.make('h264parse')
        d = Gst.ElementFactory.make('avdec_h264')

        print("asd")
        q.connect("pad-added", self.curry_decode_src_created(0))

        self.pipeline.add(f)
        self.pipeline.add(q)
        self.pipeline.add(self.p)
        self.pipeline.add(d)

        if platform.machine() == 'x86_64':
            vsink = Gst.ElementFactory.make("autovideosink", None)
        else:
            vsink = Gst.ElementFactory.make("glimagesink", None)
            vsink.set_property("qos", False)

        self.pipeline.add(vsink)
        f.link(q)
        self.p.link(d)
        d.link(vsink)

        print("init")

    def on_pad_event(self, pad, info):
        event = info.get_event()
        # if event.type == Gst.EventType.GAP or \
        if event.type == Gst.EventType.TAG:
            return Gst.PadProbeReturn.PASS
        print('event %s on pad %s', event.type, pad.get_name())
        if event.type == Gst.EventType.EOS:
            print("Pad: %s, child of: %s" %
                  (pad.get_name(), pad.parent.get_name()))
            print("Current time:", self.get_cur_time())
            # if pad.get_name() == "src_1" or pad.get_name() == "src_0":
            idx = pad.parent.get_name()[len('decoder_'):]
            print('Guessing idx: ', idx)
            GLib.idle_add(self.seek)
            return Gst.PadProbeReturn.DROP

        return Gst.PadProbeReturn.PASS

    def curry_decode_src_created(self, sink):

        def decode_src_created(element, pad):
            pad.add_probe(
                 Gst.PadProbeType.EVENT_DOWNSTREAM | Gst.PadProbeType.BLOCK,
                 self.on_pad_event
            )
            padcaps = pad.query_caps()
            if padcaps.is_empty() or padcaps.get_size() == 0:
                print("Padcaps empty!!")
                return

            padstr = padcaps.get_structure(0)
            padname = padstr.get_name()

            print("[Sink %d] Padname: %s" % (sink, padname))
            clock = self.pipeline.get_clock()
            if clock:
                runtime = clock.get_time() - self.pipeline.get_base_time()
                print("Clock! %02f" % (runtime/1000000000))
                pad.set_offset(runtime)

            if "audio" in padname:
                return
            elif "video" in padname:
                # if self.p.is_linked():
                #     print("p It's linked")
                    # self.vsinkpad.unlink(self.vsinkpad.get_peer())
                print("linking")
                pad.link(self.p.get_static_pad("sink"))

        return decode_src_created

    def get_cur_time(self):
        # delta = (self.filesrc.get_clock().get_time() - self.INITIAL_TIME)
        _, delta = self.pipeline.query_position(Gst.Format.TIME)
        return delta / 1000000000

    def seek(self):
        # flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT
        flags = Gst.SeekFlags.SEGMENT
        self.pipeline.seek_simple(Gst.Format.TIME, flags, 0)

loop = GObject.MainLoop()
p = Player()
p.pipeline.set_state(Gst.State.PLAYING)
try:
    loop.run()
except Exception as e:
    print(e)

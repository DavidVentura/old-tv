#!/usr/bin/env python3
import gi
import sys
import platform
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib

GObject.threads_init()
Gst.init(None)

class Player:
    first = {}
    count = 0
    duration = 0

    def msg(self, bus, message):
        if not message:
            return

        t = message.type
        if t != Gst.MessageType.STATE_CHANGED and t != Gst.MessageType.TAG:
            # print(t)
            pass

        if t == Gst.MessageType.ASYNC_DONE:
            if self.first:
                print("PREROLL")
                _, d = self.pipeline.query_duration(Gst.Format.TIME)
                self.duration = d
                print("Duration", d/1000000000)
                # self.seek()
                # self.first = False
                return
        elif t == Gst.MessageType.SEGMENT_DONE:
            print("Looping... IGNORED")
            for el in range(0, 2):
                d = self.pipeline.get_by_name("demuxer_%d" % el)
                _, mydur = d.query_duration(Gst.Format.TIME)
                # print(el, d.query_duration(Gst.Format.TIME))
                print(mydur, self.duration)
                if mydur == self.duration:
                    GLib.idle_add(self.seek, el)
            # sys.exit(1)
            # self.seek()
        elif t == Gst.MessageType.EOS:
            print("We got EOS on the pipeline.")
            sys.exit(1)
        elif t == Gst.MessageType.ERROR:
            err, dbg = message.parse_error()
            print("ERROR:", message.src.get_name(), " ", err.message)
            if dbg:
                print("debugging info:", dbg)
            loop.quit()
        else:
            return
            # print("Unexpected message:", t)

    def __init__(self):
        self.mainloop = GObject.MainLoop()
        self.pipeline = Gst.Pipeline.new("mypipeline")
        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message", self.msg)

        def sub_pipeline(index, filename):
            filesrc = Gst.ElementFactory.make('filesrc')
            filesrc.set_property('location', filename)
            demux = Gst.ElementFactory.make('qtdemux', 'demuxer_%d' % index)
            q = Gst.ElementFactory.make('queue')
            parse = Gst.ElementFactory.make('h264parse')
            dec = Gst.ElementFactory.make('avdec_h264')
            demux.connect("pad-added",
                          self.curry_decode_src_created(index, q, None))

            self.pipeline.add(filesrc)
            self.pipeline.add(demux)
            self.pipeline.add(q)
            self.pipeline.add(parse)
            self.pipeline.add(dec)

            filesrc.link(demux)
            q.link(parse)
            parse.link(dec)
            dec.link(self.isv)

            self.first[str(index)] = True

        self.isv = Gst.ElementFactory.make('input-selector')
        self.pipeline.add(self.isv)

        sub_pipeline(0, "/home/david/git/old-tv/noise/noise.mp4")
        # sub_pipeline(0, "/home/david/git/old-tv/noise/test.mp4")
        sub_pipeline(1, "/home/david/git/old-tv/fast22.mp4")

        if platform.machine() == 'x86_64':
            vsink = Gst.ElementFactory.make("autovideosink", None)
        else:
            vsink = Gst.ElementFactory.make("glimagesink", None)
            vsink.set_property("qos", False)

        self.pipeline.add(vsink)

        tpl_v = self.isv.get_pad_template("sink_%u")
        self.isvp = self.isv.request_pad(tpl_v, "sink_%u", None)

        self.isv.link(vsink)
        # GLib.idle_add(self.toggle, False)
        GLib.timeout_add(2000, self.toggle)


    def on_pad_event(self, pad, info):
        event = info.get_event()
        # if event.type == Gst.EventType.GAP or \
        if event.type == Gst.EventType.TAG:
            return Gst.PadProbeReturn.PASS
        print('event %s on pad %s', event.type, pad.get_name())
        # event.type == Gst.EventType.SEGMENT_DONE or 
        if event.type == Gst.EventType.EOS:
            print("Pad: %s, child of: %s" %
                  (pad.get_name(), pad.parent.get_name()))
            print("Current time:", self.get_cur_time())
            idx = pad.parent.get_name()[len('decoder_'):]
            print('Guessing idx: ', idx)
            GLib.idle_add(self.seek, idx)
            return Gst.PadProbeReturn.DROP

        return Gst.PadProbeReturn.PASS

    def curry_decode_src_created(self, sink, velem, aelem):

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
                pad.set_offset(clock.get_time() + self.duration) # FIXME?

            if "audio" in padname:
                return
            elif "video" in padname:
                spad = velem.get_static_pad("sink")
                if spad.is_linked():
                    print("It's linked")
                    spad.unlink(spad.get_peer())
                print("linking video")
                pad.link(spad)

        return decode_src_created

    def get_cur_time(self):
        # delta = (self.filesrc.get_clock().get_time() - self.INITIAL_TIME)
        _, delta = self.pipeline.query_position(Gst.Format.TIME)
        return delta / 1000000000

    def seek(self, idx):
        idx = str(idx)
        print("seeking %s" % idx)
        demuxer = self.pipeline.get_by_name("demuxer_%s" % idx)
        # demuxer = self.isv.get_static_pad('src_%s' % idx)
        if self.first[idx]:
            flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT
            self.first[idx] = False
            print("NOT FIRST!!!!!!!!!")
        else:
            # flags = Gst.SeekFlags.SEGMENT
            flags = Gst.SeekFlags.ACCURATE | Gst.SeekFlags.SEGMENT
        # self.pipeline.seek_simple(Gst.Format.TIME, flags, 0)
        demuxer.seek_simple(Gst.Format.TIME, flags, 0)

    def toggle(self, ret=True):
        print("Togglin")
        self.count += 1
        self.count = self.count % 2
        print(self.count)
        newpad = self.isv.get_static_pad('sink_%d' % self.count)
        self.isv.set_property('active-pad', newpad)
        return ret

loop = GObject.MainLoop()
p = Player()
p.pipeline.set_state(Gst.State.PLAYING)
try:
    loop.run()
except Exception as e:
    print(e)

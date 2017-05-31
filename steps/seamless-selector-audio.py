#!/usr/bin/env python3
import ctypes
import gi
import sys
import platform
gi.require_version('Gst', '1.0')
try:
    gi.require_version('GstGL', '1.0')
    from gi.repository import GObject, Gst, GLib, GstGL
except:
    from gi.repository import GObject, Gst, GLib

GObject.threads_init()
Gst.init(None)

class Player:
    FINISHING_FILE = '0'
    first = {}
    count = 0
    duration = 0
    sources = ["/home/david/git/old-tv/noise/test.mp4",
               "/home/david/git/old-tv/fast22.mp4",
               "/home/david/git/old-tv/fast4.mp4",
               "/home/david/git/old-tv/fast5.mp4",
               "/home/david/git/old-tv/fast88.mp4"
	       ]

    def msg(self, bus, message):
        if not message:
            return

        t = message.type
        if t != Gst.MessageType.STATE_CHANGED and t != Gst.MessageType.TAG:
            # print(t)
            pass

        if t == Gst.MessageType.ASYNC_DONE:
            for key in self.first:
                if self.first[key]:
                    GLib.idle_add(self.seek, key)
                    self.first[key] = False
                    break
        elif t == Gst.MessageType.SEGMENT_DONE:
            print("Looping... src: ", message.src.name)
            GLib.idle_add(self.seek, self.FINISHING_FILE)
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

        enable_bcm = (platform.machine() != 'x86_64')

        def sub_pipeline(index, filename):
            filesrc = Gst.ElementFactory.make('filesrc')
            filesrc.set_property('location', filename)
            demux = Gst.ElementFactory.make('qtdemux', 'demuxer_%d' % index)
            vq = Gst.ElementFactory.make('queue')
            vparse = Gst.ElementFactory.make('h264parse')
            if enable_bcm:
                vdec = Gst.ElementFactory.make('omxh264dec')
            else:
                vdec = Gst.ElementFactory.make('avdec_h264')

            aq = Gst.ElementFactory.make('queue')
            aparse = Gst.ElementFactory.make('mpegaudioparse')
            adec = Gst.ElementFactory.make('avdec_mp3')

            demux.connect("pad-added",
                          self.curry_decode_src_created(index, vq, aq))

            self.pipeline.add(filesrc)
            self.pipeline.add(demux)
            self.pipeline.add(vq)
            self.pipeline.add(vparse)
            self.pipeline.add(vdec)

            self.pipeline.add(aq)
            self.pipeline.add(aparse)
            self.pipeline.add(adec)

            filesrc.link(demux)

            # Video stuff
            vq.link(vparse)
            vparse.link(vdec)
            vdec.link(self.isv)

            # Audio stuff
            aq.link(aparse)
            aparse.link(adec)
            adec.link(self.isa)

            self.first[str(index)] = True

        self.isv = Gst.ElementFactory.make('input-selector')
        self.isa = Gst.ElementFactory.make('input-selector')
        self.pipeline.add(self.isv)
        self.pipeline.add(self.isa)

        for f in range(0, len(self.sources)):
            sub_pipeline(f, self.sources[f])

        if not enable_bcm:
            vsink = Gst.ElementFactory.make("autovideosink", None)
        else:
            vsink = Gst.ElementFactory.make("glimagesink", None)
            vsink.set_property("qos", False)

        self.pipeline.add(vsink)

        asink = Gst.ElementFactory.make("alsasink", None)
        self.pipeline.add(asink)

        tpl_a = self.isa.get_pad_template("sink_%u")
        tpl_v = self.isv.get_pad_template("sink_%u")
        self.isvp = self.isv.request_pad(tpl_v, "sink_%u", None)
        self.isap = self.isa.request_pad(tpl_a, "sink_%u", None)

        DISPLAY_CLOCK = False
        if DISPLAY_CLOCK:
            clock = Gst.ElementFactory.make('clockoverlay')
            self.pipeline.add(clock)

            self.isv.link(clock)
            clock.link(vsink)
        else:
            self.isv.link(vsink)

        self.isa.link(asink)

        if enable_bcm:
            # Raspberry pi:  Create a dispmanx element for gstreamer
            # to render to and pass it to gstreamer
            import bcm

            bus = self.pipeline.get_bus()
            width, height = bcm.get_resolution()

            # Create a window slightly smaller than fullscreen
            nativewindow = bcm.create_native_window(0, 5, width, height-10, alpha_opacity=0)
            win_handle = ctypes.addressof(nativewindow)

            def on_sync_message(bus, msg):
                if msg.get_structure().get_name() == 'prepare-window-handle':
                    _sink = msg.src
                    _sink.set_window_handle(win_handle)
                    _sink.set_render_rectangle(0, 0, nativewindow.width, nativewindow.height)

            bus.enable_sync_message_emission()
            bus.connect('sync-message::element', on_sync_message)
        else:
            nativewindow, win_handle = None, None

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
            idx = pad.parent.get_name()[len('decoder_'):]
            print('Guessing idx: ', idx)
            self.FINISHING_FILE = str(idx)
            GLib.idle_add(self.seek, idx)
            return Gst.PadProbeReturn.DROP

        if event.type == Gst.EventType.SEGMENT_DONE:
            print("PROBE: Segment")
            print("Pad: %s, child of: %s" %
                  (pad.get_name(), pad.parent.get_name()))
            idx = pad.parent.get_name().split("_")[1]
            print("seeking SEGMENT DONE", idx)
            self.FINISHING_FILE = idx
            GLib.idle_add(self.seek, self.FINISHING_FILE)
            return Gst.PadProbeReturn.PASS

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
                # pad.set_offset(clock.get_time() + self.duration) # FIXME?

            if "audio" in padname:
                spad = aelem.get_static_pad("sink")
                print("linking audio")
            elif "video" in padname:
                spad = velem.get_static_pad("sink")
                print("linking video")

            if spad.is_linked():
                print("It's linked")
                spad.unlink(spad.get_peer())
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
        else:
            flags = Gst.SeekFlags.SEGMENT
        # self.pipeline.seek_simple(Gst.Format.TIME, flags, 0)
        demuxer.seek_simple(Gst.Format.TIME, flags, 0)
        return False  # Timeout add

    def toggle(self, target):
        target = max(target)
        target = min(target, len(self.sources) - 1)
        print("Toggling %d" % target)
        newpad = self.isv.get_static_pad('sink_%d' % target)
        self.isv.set_property('active-pad', newpad)

        newpad = self.isa.get_static_pad('sink_%d' % target)
        self.isa.set_property('active-pad', newpad)

    def start(self):
        loop = GObject.MainLoop()
        p = Player()
        p.pipeline.set_state(Gst.State.PLAYING)
        try:
            loop.run()
        except Exception as e:
            print(e)

if __name__ == '__main__':
    p = Player()
    p.start()

#!/usr/bin/env python3
import ctypes
import gi
import sys
import os
import platform
gi.require_version('Gst', '1.0')
try:
    gi.require_version('GstGL', '1.0')
    from gi.repository import GObject, Gst, GLib, GstGL
except:
    from gi.repository import GObject, Gst, GLib

GObject.threads_init()
Gst.init(None)


def debug(msg):
    if False:
        print(msg)


class Player:
    FINISHING_FILE = '0'
    first = {}
    spads = {}
    current_points = {}

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
                    GLib.idle_add(self.seek, key, self.starting_points[key])
                    self.first[key] = False
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
                print("restarting program:", dbg)
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            return
            # print("Unexpected message:", t)

    def __init__(self, starting_points, sources):
        self.starting_points = starting_points
        self.sources = sources
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
            # vsink = Gst.ElementFactory.make("autovideosink", None)
            vsink = Gst.ElementFactory.make("xvimagesink", None)
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
            nativewindow = bcm.create_native_window(0, 0, width, height, alpha_opacity=0)
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
        debug('event %s on pad %s' % (event.type, pad.get_name()))
        if event.type == Gst.EventType.EOS:
            debug("Pad: %s, child of: %s" % (pad.get_name(), pad.parent.get_name()))
            debug("Current time: %s" % self.get_cur_time())
            idx = pad.parent.get_name()[len('decoder_'):]
            debug('Guessing idx: %s' % idx)
            self.FINISHING_FILE = str(idx)
            GLib.idle_add(self.seek, idx)
            return Gst.PadProbeReturn.DROP

        if event.type == Gst.EventType.SEGMENT_DONE:
            debug("PROBE: Segment")
            debug("Pad: %s, child of: %s" % (pad.get_name(), pad.parent.get_name()))
            idx = pad.parent.get_name().split("_")[1]
            debug("seeking SEGMENT DONE %s" % idx)
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
                # pad.set_offset(clock.get_time() + self.duration) # FIXME?

            if "audio" in padname:
                spad = aelem.get_static_pad("sink")
                print("linking audio")
            elif "video" in padname:
                spad = velem.get_static_pad("sink")
                print("linking video")
                GObject.timeout_add(2000 + 1000 * sink, self.setup_vspad,
                                    sink, spad.get_parent_element())

            if spad.is_linked():
                print("It's linked")
                spad.unlink(spad.get_peer())
            pad.link(spad)

        return decode_src_created

    def get_cur_time(self):
        # delta = (self.filesrc.get_clock().get_time() - self.INITIAL_TIME)
        _, delta = self.pipeline.query_position(Gst.Format.TIME)
        return delta / Gst.SECOND

    def seek(self, idx, t=0):
        idx = str(idx)
        debug("seeking %s to %d" % (idx, t))
        demuxer = self.pipeline.get_by_name("demuxer_%s" % idx)
        # demuxer = self.isv.get_static_pad('src_%s' % idx)
        if t != 0:
            print("idx: %s seeking special" % idx)
            flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT
        else:
            if self.first[idx]:
                flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT
            else:
                flags = Gst.SeekFlags.SEGMENT
        # self.pipeline.seek_simple(Gst.Format.TIME, flags, 0)
        demuxer.seek_simple(Gst.Format.TIME, flags, t * Gst.SECOND)
        return False  # Timeout add

    def toggle(self, target):
        target = max(0, target)
        target = min(target, len(self.sources) - 1)
        debug("Toggling %d" % target)
        newpad = self.isv.get_static_pad('sink_%d' % target)
        self.isv.set_property('active-pad', newpad)

        newpad = self.isa.get_static_pad('sink_%d' % target)
        self.isa.set_property('active-pad', newpad)

    def start(self):
        loop = GObject.MainLoop()
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            loop.run()
        except Exception as e:
            print(e)
            loop.quit()

    def setup_vspad(self, idx, elem):
        print("setting up %s" % idx)
        self.spads[idx] = elem
        return False  # For timeout_add

    def update_timings(self):
        for key in self.spads:
            _, t = self.spads[key].query_position(Gst.Format.TIME)
            val = t / Gst.SECOND
            self.current_points[key] = val
            print(key, val)
        return self.current_points

    def get_current_channel(self):
        name = self.isv.get_property('active-pad').get_name()
        return name.split("_")[1]


if __name__ == '__main__':
    p = Player()
    import threading
    import time
    th = threading.Thread(target=p.start)
    th.daemon = True
    th.start()
    v = 0
    time.sleep(2)

    while th.is_alive():
        p.toggle(v)
        v = v + 1
        v = v % len(p.sources)
        if v == 0:
            p.update_timings()
        time.sleep(1.5)
    th.join()

import gi
import sys
import platform
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib

GObject.threads_init()
Gst.init(None)


class Player:
    count = 0

    def msg(self, bus, message):
        if not message:
            return

        t = message.type
        if t == Gst.MessageType.EOS:
            print("We got EOS on the pipeline.")
            sys.exit(1)
        elif t == Gst.MessageType.ERROR:
            err, dbg = message.parse_error()
            print("ERROR:", message.src.get_name(), " ", err.message)
            if dbg:
                print("debugging info:", dbg)
        print(t)

    def __init__(self):
        self.mainloop = GObject.MainLoop()
        self.pipeline = Gst.Pipeline.new("mypipeline")

        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message", self.msg)

        s = Gst.ElementFactory.make('uridecodebin', 'decoder')
        s.set_property('uri', "file:///home/david/git/old-tv/noise/out.mp4")
        s.connect("pad-added", self.on_pad_added)
        self.pipeline.add(s)

        if platform.machine() == 'x86_64':
            self.vsink = Gst.ElementFactory.make("autovideosink", None)
        else:
            self.vsink = Gst.ElementFactory.make("glimagesink", None)
            self.vsink.set_property("qos", False)

        self.asink = Gst.ElementFactory.make("autoaudiosink", None)

        self.vqueue = Gst.ElementFactory.make("queue", None)
        self.aqueue = Gst.ElementFactory.make("queue", None)

        self.pipeline.add(self.vqueue)
        self.pipeline.add(self.aqueue)

        self.pipeline.add(self.vsink)
        self.pipeline.add(self.asink)

        self.vqueue.link(self.vsink)
        self.aqueue.link(self.asink)


    def next_file(self):
        self.pipeline.set_state(Gst.State.READY)
        d = self.pipeline.get_by_name('decoder')
        d.set_property('uri', d.get_property('uri'))
        self.pipeline.set_state(Gst.State.PLAYING)
        print('NEXT_FILE READY')

    def on_pad_event(self, pad, info):
        event = info.get_event()

        if event.type == Gst.EventType.EOS:
            print('scheduling next track and dropping EOS-Event')
            GObject.idle_add(self.next_file)
            return Gst.PadProbeReturn.DROP

        return Gst.PadProbeReturn.PASS

    def on_pad_added(self, src, pad):
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

        sink = None
        if "video" in padname:
            sink = self.vqueue.get_static_pad("sink")
        if "audio" in padname:
            sink = self.aqueue.get_static_pad("sink")

        if sink is None:
            print("no sink")
            return  # ????

        clock = self.pipeline.get_clock()
        if clock:
            duration = self.pipeline.query_duration(Gst.Format(Gst.Format.TIME))[1]
            print("Duration %s" % duration)
            print("ctime %s, btime: %s" % 
                (clock.get_time(), self.pipeline.get_base_time()))
            runtime = clock.get_time() - self.pipeline.get_base_time()
            print('setting pad offset to pipeline runtime: %d' % runtime)
            pad.set_offset(runtime)
            # pad.set_offset(duration)
        pad.link(sink)

    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop.run()


if __name__ == '__main__':
    p = Player()
    p.run()

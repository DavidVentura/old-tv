import gi
import sys
import platform
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib

GObject.threads_init()
Gst.init(None)


class Player:
    count = 2
    values = [2, 4, 5, 8]

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
#        print(t)

    def __init__(self):
        self.mainloop = GObject.MainLoop()
        self.pipeline = Gst.Pipeline.new("mypipeline")

        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message", self.msg)

        self.s = Gst.ElementFactory.make('tcpclientsrc', 'src')
        self.s.set_property('host', "0.0.0.0")
        self.s.set_property('port', 2000)
        self.pipeline.add(self.s)

        if platform.machine() == 'x86_64':
            self.vsink = Gst.ElementFactory.make("autovideosink", None)
        else:
            self.vsink = Gst.ElementFactory.make("glimagesink", None)
            self.vsink.set_property("qos", False)

        self.dec = Gst.ElementFactory.make("decodebin", None)
        self.dec.connect("pad-added", self.on_pad_added)
        self.pipeline.add(self.dec)

        self.s.link(self.dec)

        self.asink = Gst.ElementFactory.make("autoaudiosink", None)

        self.pipeline.add(self.vsink)
        self.pipeline.add(self.asink)

        # GObject.timeout_add(2000, self.change_port)

    def change_port(self):
        self.count = 1 + (self.count % 10)

        print(self.count)
        self.pipeline.set_state(Gst.State.READY)
        if self.count not in self.values:
            print("snow")
            self.s.set_property('port', 10000)
        else:
            self.s.set_property('port', self.count*1000)
        self.pipeline.set_state(Gst.State.PLAYING)
        return True

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
            # FIXME RESTART
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
            sink = self.vsink.get_static_pad("sink")
        if "audio" in padname:
            sink = self.asink.get_static_pad("sink")

        if sink is None:
            print("no sink")
            return  # ????

        clock = self.pipeline.get_clock()
        if clock:
            print("ctime %s, btime: %s" %
                (clock.get_time(), self.pipeline.get_base_time()))
            runtime = clock.get_time() - self.pipeline.get_base_time()
            print('setting pad offset to pipeline runtime: %d' % runtime)
            # pad.set_offset(runtime)
            # pad.set_offset(duration)
        pad.link(sink)

    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop.run()


if __name__ == '__main__':
    p = Player()
    p.run()

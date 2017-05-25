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

    def __init__(self):
        self.mainloop = GObject.MainLoop()
        self.pipeline = Gst.Pipeline.new("mypipeline")

        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message", self.msg)

        patterns = ["smpte", "snow", "black", "white"]
        waves = ["sine", "white-noise", "silence", "pink-noise"]
        for c in range(0, 4):
            s = Gst.ElementFactory.make('videotestsrc', 'video_%d' % c)
            s.set_property('pattern', patterns[c])
            s.set_property('is-live', True)
            self.pipeline.add(s)

            a = Gst.ElementFactory.make('audiotestsrc', 'audio_%d' % c)
            a.set_property('is-live', True)
            a.set_property('wave', waves[c])
            self.pipeline.add(a)

        self.input_v = Gst.ElementFactory.make('input-selector', 'isv')
        self.pipeline.add(self.input_v)

        self.input_a = Gst.ElementFactory.make('input-selector', 'isa')
        self.pipeline.add(self.input_a)

        for c in range(0, 4):
            self.pipeline.get_by_name("video_%d" % c).link(self.input_v)
            self.pipeline.get_by_name("audio_%d" % c).link(self.input_a)


        if platform.machine() == 'x86_64':
            vsink = Gst.ElementFactory.make("autovideosink", None)
        else:
            vsink = Gst.ElementFactory.make("glimagesink", None)
            vsink.set_property("qos", False)

        self.pipeline.add(vsink)

        asink = Gst.ElementFactory.make("autoaudiosink", None)
        self.pipeline.add(asink)

        self.input_v.link(vsink)
        self.input_a.link(asink)

        tpl_v = self.input_v.get_pad_template("sink_%u")
        tpl_a = self.input_a.get_pad_template("sink_%u")

        self.vsinks = []
        self.asinks = []
        for c in range(0, 4):
            self.vsinks.append(self.input_v.request_pad(tpl_v, "sink_%u", None))
            self.asinks.append(self.input_a.request_pad(tpl_a, "sink_%u", None))

    def toggle(self):
        print("Togglin")
        self.count += 1
        self.count = self.count % 4

        newpad = self.input_v.get_static_pad('sink_%d' % self.count)
        self.input_v.set_property('active-pad', newpad)

        newpad = self.input_a.get_static_pad('sink_%d' % self.count)
        self.input_a.set_property('active-pad', newpad)
        return True

    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        GLib.timeout_add(400, self.toggle)
        self.mainloop.run()

if __name__ == '__main__':
    p = Player()
    p.run()

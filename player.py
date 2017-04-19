import gi
import sys
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

GObject.threads_init()
Gst.init(None)


class Player:
    NEXT_FILE = None
    LAST_CHAPTER_TIME = 0
    DURATION = 0
    CHANGING_URI = False

    def msg(self, bus, message):
        t = message.type
        if t == Gst.MessageType.STATE_CHANGED:
            return
        if t == Gst.MessageType.EOS:
            print("We got EOS on the pipeline.")
            sys.exit(1)
        # print(message.type)
        # print(message.parse())
        return

    def __init__(self, on_finished, on_duration):
        self.on_finished = on_finished
        self.on_duration = on_duration

        self.mainloop = GObject.MainLoop()
        self.pipeline = Gst.Pipeline.new("mypipeline")
        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message", self.msg)

        self.filesrc = Gst.ElementFactory.make("uridecodebin", "filesrc")
        self.filesrc.connect("pad-added", self.decode_src_created)
        self.pipeline.add(self.filesrc)

        self.vconv = Gst.ElementFactory.make("videoconvert", None)
        self.pipeline.add(self.vconv)

        vscale = Gst.ElementFactory.make("videoscale", None)
        self.pipeline.add(vscale)

        #vcaps = Gst.Caps.from_string("video/x-raw,width=1280,height=1024")
        vcaps = Gst.Caps.from_string("video/x-raw,width=656,height=416")
        vfilter = Gst.ElementFactory.make("capsfilter", "vfilter")
        vfilter.set_property("caps", vcaps)
        self.pipeline.add(vfilter)

        self.input_v = Gst.ElementFactory.make("input-selector", "isv")
        self.pipeline.add(self.input_v)

        vsink = Gst.ElementFactory.make("autovideosink", "vsink")
        self.pipeline.add(vsink)

        self.input_v.link(vsink)

        blankvideo = Gst.ElementFactory.make("videotestsrc", "snow")
        blankvideo.set_property("pattern", "snow")
        # blankvideo.set_property("is-live", True)
        self.pipeline.add(blankvideo)

        vfilter2 = Gst.ElementFactory.make("capsfilter", "vfilter2")
        vfilter2.set_property("caps", vcaps)
        self.pipeline.add(vfilter2)
        blankvideo.link(vfilter2)

        self.toverlay = Gst.ElementFactory.make("textoverlay", "toverlay")
        self.toverlay.set_property("text", "Channel")
        self.toverlay.set_property("halignment", "right")
        self.toverlay.set_property("valignment", "top")
        self.toverlay.set_property("font-desc", "Sans 32")
        # self.toverlay.set_property("shaded-background", True)
        self.pipeline.add(self.toverlay)

        vfilter2.link(self.toverlay)

        blankaudio = Gst.ElementFactory.make("audiotestsrc", "noise")
        blankaudio.set_property("wave", "white-noise")
        blankaudio.set_property("volume", 0.02)
        # blankaudio.set_property("is-live", True)
        self.pipeline.add(blankaudio)

        self.input_a = Gst.ElementFactory.make("input-selector", "isa")
        self.pipeline.add(self.input_a)

        asink = Gst.ElementFactory.make("autoaudiosink", "asink")
        self.pipeline.add(asink)

        self.input_a.link(asink)
        #vfilter.link(vsink)
        #blankvideo.link(self.input_v)
        self.toverlay.link(self.input_v)
        blankaudio.link(self.input_a)

        tpl_v = self.input_v.get_pad_template("sink_%u")
        self.ivpad = self.input_v.request_pad(tpl_v, "sink_%u", None)

        tpl_a = self.input_a.get_pad_template("sink_%u")
        self.iapad = self.input_a.request_pad(tpl_a, "sink_%u", None)


        # vcaps = Gst.Caps.from_string("video/x-raw,width=576,height=432")
        # vcaps = Gst.Caps.from_string("video/x-raw,width=640,height=480")
        # vfilter = Gst.ElementFactory.make("capsfilter", "vfilter")
        # vfilter.set_property("caps", vcaps)
        # self.pipeline.add(vfilter)

        # self.input_v.link(vfilter)

        # for c in self.pipeline.children:
        #    print(c.get_name())
        # self.change_uri(self.get_next_file())

    def on_pad_event(self, pad, info):
        event = info.get_event()
        # print('event %s on pad %s', event.type, pad)

        if event.type == Gst.EventType.EOS:
            print("Pad: %s, child of: %s" %
                  (pad.get_name(), pad.parent.get_name()))
            print("Current time:", self.get_cur_time())
            print("Duration", self.DURATION)
            print('scheduling next track and dropping EOS-Event')
            # if pad.get_name() == "src_1" or pad.get_name() == "src_0":
            if self.DURATION <= self.get_cur_time() + 5 and \
               self.DURATION > 0:
                if self.on_finished is not None:
                    self.on_finished()

            return Gst.PadProbeReturn.DROP

        return Gst.PadProbeReturn.PASS

    def decode_src_created(self, element, pad):
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

        # print("Padname:", padname)
        if "audio" in padname:
            pad.link(self.iapad)
        elif "video" in padname:
            pad.link(self.ivpad)

    def channel(self):
        print("Switching to Channel. Current clock: ", self.get_cur_time())
        snowpad = self.input_v.get_static_pad('sink_%d' % 1)
        self.input_v.set_property('active-pad', snowpad)

        snowpad = self.input_a.get_static_pad('sink_%d' % 1)
        self.input_a.set_property('active-pad', snowpad)

        GObject.timeout_add(150, self.seek, self.LAST_CHAPTER_TIME)
        GObject.timeout_add(300, self.update_duration)

    def get_cur_time(self):
        # delta = (self.filesrc.get_clock().get_time() - self.INITIAL_TIME)
        _, delta = self.pipeline.query_position(Gst.Format.TIME)
        return delta / 1000000000

    def snow(self, channel='?'):
        self.toverlay.set_property('text', channel)
        self.LAST_CHAPTER_TIME = self.get_cur_time()

        print("Switching to snow. Current clock: ", self.get_cur_time())
        snowpad = self.input_v.get_static_pad('sink_%d' % 0)
        self.input_v.set_property('active-pad', snowpad)

        snowpad = self.input_a.get_static_pad('sink_%d' % 0)
        self.input_a.set_property('active-pad', snowpad)

    # running the shit
    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop.run()

    def _change_uri(self, start_time, duration):
        print('change uri:', start_time, duration)
        self.LAST_CHAPTER_TIME = start_time
        self.DURATION = duration
        self.pipeline.set_state(Gst.State.READY)
        self.filesrc.set_property("uri", self.NEXT_FILE)
        self.pipeline.set_state(Gst.State.PLAYING)
        print('Calling channel now. LCT:', self.LAST_CHAPTER_TIME)
        self.channel()
        self.CHANGING_URI = False
        return False  # Avoid calling repeatedly

    def change_uri(self, start_time=0, duration=0):
        if self.CHANGING_URI:
            print("Can't nest change_uri calls")
            return
        self.CHANGING_URI = True
        GObject.idle_add(self._change_uri, start_time, duration)

    def set_next_file(self, uri):
        print("Current  Next file:", self.NEXT_FILE)
        print("New      Next file:", uri)
        self.NEXT_FILE = uri

    def update_duration(self):
        _, d = self.filesrc.query_duration(Gst.Format.TIME)
        self.DURATION = d / 1000000000
        print("Duration:", self.DURATION)
        if self.on_duration is not None:
            self.on_duration(self.DURATION)
        return False  # To get the timeout interval to stop

    def seek(self, seek_time_secs):
        print("Asked to seek to: ", seek_time_secs)
        seek_time_secs = min(seek_time_secs, max(self.DURATION - 1, 0))
        print("Seeking to", seek_time_secs)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH,
                                  seek_time_secs * Gst.SECOND)
        #   | Gst.SeekFlags.KEY_UNIT,
        return False  # To get the timeout interval to stop

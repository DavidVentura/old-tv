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
    CUR_STATE = None
    BUSY = False

    def msg(self, bus, message):
        if not message:
            return

        t = message.type
        if t != Gst.MessageType.STATE_CHANGED and t != Gst.MessageType.TAG:
            print(t)
            pass

        if t == Gst.MessageType.EOS:
            print("We got EOS on the pipeline.")
            sys.exit(1)
        elif t == Gst.MessageType.ASYNC_DONE:
            print("############# Async done, cur state:", self.CUR_STATE)
            self.BUSY = False
        elif t == Gst.MessageType.QOS:
            return
        elif t == Gst.MessageType.ERROR:
            err, dbg = message.parse_error()
            print("ERROR:", message.src.get_name(), " ", err.message)
            self.BUSY = False
            if dbg:
                print("debugging info:", dbg)
        elif t == Gst.MessageType.STATE_CHANGED:
            # we are only interested in STATE_CHANGED messages from
            # the pipeline
            if message.src == self.pipeline:
                # IF NEW_STATE == PAUSED => SEEK
                old_state, new_state, pending_state = message.parse_state_changed()
                print("Pipeline state changed from {0:s} to {1:s}".format(
                    Gst.Element.state_get_name(old_state),
                    Gst.Element.state_get_name(new_state)))
                self.CUR_STATE = new_state
                # old_state != Gst.State.READY and
                if old_state != Gst.State.NULL and new_state == Gst.State.READY:
                    print("!!")
                    self.filesrc.set_property("uri", self.NEXT_FILE)
                    print("PAUSING")
                    self.pipeline.set_state(Gst.State.PAUSED)
                    print("PAUSED")
                    self.CHANGING_URI = False
                    print("URI = CHANGED")
                    pass

                if new_state == Gst.State.PAUSED and old_state == Gst.State.READY:
                    print("The stream is paused. I Must seek")
                    GObject.idle_add(self.seek, self.LAST_CHAPTER_TIME)
            else:
                # print("I don't care")
                return
        elif t == Gst.MessageType.TAG:
            return
            tag = message.parse_tag()
            count = tag.n_tags()
            print(count)
            for i in range(0, count):
                print(tag.nth_tag_name(i))
        elif t == Gst.MessageType.DURATION_CHANGED:
            GObject.idle_add(self.update_duration)
        elif t == Gst.MessageType.STREAM_STATUS:
            #print("STATUS:", message.parse_stream_status())
            pass
        elif t == Gst.MessageType.STREAM_START:
            print("STARTED MESSAGE")
            if self.DURATION == 0:
                print("Duration is 0!")
                GObject.idle_add(self.update_duration)

        elif t == Gst.MessageType.STREAM_STATUS:
            return
            print("STATUS:")
            print(message.parse_stream_status())
        else:
            #print("Unexpected message:", t)
            pass

    def __init__(self, blank_uri, on_finished, on_duration):
        print(blank_uri)
        self.blank_uri = blank_uri
        self.on_finished = on_finished
        self.on_duration = on_duration

        self.mainloop = GObject.MainLoop()
        # p = """videoconvert ! videoscale ! video/x-raw,width=656,height=416"""
        # self.pipeline = Gst.parse_launch(p)
        self.pipeline = Gst.Pipeline.new("mypipeline")

        self.filesrc = Gst.ElementFactory.make('uridecodebin', None)
        # self.pipeline.get_by_name('udb')
        self.filesrc.set_property('uri', blank_uri)
        self.filesrc.connect("pad-added", self.decode_src_created)
        # self.pipeline.add(self.filesrc)

        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message", self.msg)

        #glupload = Gst.ElementFactory.make("glupload", None)
        #glcs = Gst.ElementFactory.make("glcolorscale", None)
        # glcs = Gst.ElementFactory.make("glcolorconvert", None)
        #convert = Gst.ElementFactory.make("videoconvert", None)
        #scale = Gst.ElementFactory.make("videoscale", None)
        #rate = Gst.ElementFactory.make("videorate", None)
        #capsfilter = Gst.ElementFactory.make("capsfilter", None)
        # gldownload = Gst.ElementFactory.make("gldownload", None)

        #caps = Gst.Caps.from_string("video/x-raw(memory:GLMemory),width=800,height=600")
        #caps = Gst.Caps.from_string("video/x-raw(memory:GLMemory), framerate=(fraction)25/1")
        #capsfilter.set_property("caps", caps)
        # caps = video/x-raw(memory:GLMemory), format=(string)RGBA, width=(int)640, height=(int)480,
        # interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, colorimetry=(string)sRGB,
        # framerate=(fraction)25/1

        #vsink = Gst.ElementFactory.make("autovideosink", None)
        vsink = Gst.ElementFactory.make("glimagesink", None)
        vsink.set_property("qos", False)
        #vsink.set_property("enable-last-sample", False)
        #vsink.set_property("handle-events", False)
        #vsink.set_property("render-delay", 100000)



        self.pipeline.add(self.filesrc)
        #self.pipeline.add(glupload)
        #self.pipeline.add(glcs)
        # self.pipeline.add(convert)
        # self.pipeline.add(scale)
        # self.pipeline.add(rate)
        #self.pipeline.add(capsfilter)
        #self.pipeline.add(gldownload)
        self.pipeline.add(vsink)

        #glupload.link(glcs)
        #glupload.link(rate)
        #glcs.link(rate)
        #glcs.link(capsfilter)
        #convert.link(scale)
        #scale.link(rate)
        #rate.link(capsfilter)
        #capsfilter.link(vsink)
        #capsfilter.link(gldownload)
        # gldownload.link(vsink)

        asink = Gst.ElementFactory.make("autoaudiosink", None)
        self.pipeline.add(asink)

        self.vsinkpad = vsink.get_static_pad("sink")
        #self.vsinkpad = glupload.get_static_pad("sink")
        #self.vsinkpad = convert.get_static_pad("sink")
        self.asinkpad = asink.get_static_pad("sink")

    def on_pad_event(self, pad, info):
        event = info.get_event()
        #if event.type == Gst.EventType.GAP or \
        if event.type == Gst.EventType.SEGMENT or \
           event.type == Gst.EventType.TAG:
            return Gst.PadProbeReturn.PASS
        # print('event %s on pad %s', event.type, pad)
        if event.type == Gst.EventType.EOS:
            print("Pad: %s, child of: %s" %
                  (pad.get_name(), pad.parent.get_name()))
            print("Current time:", self.get_cur_time())
            print("Duration", self.DURATION)
            print('scheduling next track and dropping EOS-Event')
            # if pad.get_name() == "src_1" or pad.get_name() == "src_0":
            if self.DURATION <= self.get_cur_time() + 5 and self.DURATION > 0:
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
        #clock = self.pipeline.get_clock()
        #if clock:
        #    runtime = clock.get_time() - self.pipeline.get_base_time()
        #    print('setting pad offset to pipeline runtime: %sns' % runtime)
        #    pad.set_offset(runtime)

        padstr = padcaps.get_structure(0)
        padname = padstr.get_name()

        print("Padname:", padname)
        if "audio" in padname:
            if self.asinkpad.is_linked():
                #self.asinkpad.unlink(self.asinkpad.get_peer())
                pass

            pad.link(self.asinkpad)
        elif "video" in padname:
            if self.vsinkpad.is_linked():
                #self.vsinkpad.unlink(self.vsinkpad.get_peer())
                pass

            pad.link(self.vsinkpad)

    def get_cur_time(self):
        # delta = (self.filesrc.get_clock().get_time() - self.INITIAL_TIME)
        _, delta = self.pipeline.query_position(Gst.Format.TIME)
        return delta / 1000000000

    def snow(self):
        self.LAST_CHAPTER_TIME = self.get_cur_time()

        print("Switching to snow. Current clock: ", self.get_cur_time())
        self.NEXT_FILE = self.blank_uri
        self.change_uri()

    # running the shit
    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop.run()

    def _change_uri(self, start_time, duration):
        print('change uri:', start_time, duration)
        self.LAST_CHAPTER_TIME = start_time
        self.DURATION = duration
        print("READYING")
        self.pipeline.set_state(Gst.State.READY)
        print("READIED")

        #print('Calling channel now. LCT:', self.LAST_CHAPTER_TIME)
        return False  # Avoid calling repeatedly

    def change_uri(self, start_time=0, duration=10):
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
        val = d / 1000000000
        if val == 0:
            return
        self.DURATION = val
        print("Duration:", self.DURATION)
        if self.on_duration is not None:
            self.on_duration(self.DURATION)
        return False  # To get the timeout interval to stop

    def seek(self, seek_time_secs):
        print("Asked to seek to: ", seek_time_secs)
        if self.BUSY:
            print("IM BUSY!!!!!!!")
            return
        seek_time_secs = min(seek_time_secs, max(self.DURATION - 1, 0))
        if abs(seek_time_secs - self.get_cur_time()) < 0.5:
            print("########## Not seeking < 0.5s")
            pass

        #self.BUSY = True
        print("Seeking to", seek_time_secs)
        res = self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH,
                                  seek_time_secs * Gst.SECOND)
        #res = self.pipeline.seek(1, Gst.Format.TIME,
        #        Gst.SeekFlags.FLUSH,
        #        Gst.SeekType.SET,
        #        seek_time_secs * Gst.SECOND,
        #        Gst.SeekType.NONE,
        #        -1)
        print("Seeking result", res)
        #   | Gst.SeekFlags.KEY_UNIT,
        self.pipeline.set_state(Gst.State.PLAYING)
        return False  # To get the timeout interval to stop

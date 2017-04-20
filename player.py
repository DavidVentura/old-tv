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
    MUST_SEEK = False
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
        elif t == Gst.MessageType.STATE_CHANGED:
            # we are only interested in STATE_CHANGED messages from
            # the pipeline
            if message.src == self.pipeline:
                # IF NEW_STATE == PAUSED => SEEK
                old_state, new_state, pending_state = message.parse_state_changed()
                # print("Pipeline state changed from {0:s} to {1:s}".format(
                #     Gst.Element.state_get_name(old_state),
                #     Gst.Element.state_get_name(new_state)))
                if self.MUST_SEEK and new_state == Gst.State.PAUSED:
                    print("The stream is paused. I Must seek")
                    self.seek(self.LAST_CHAPTER_TIME)
                    self.MUST_SEEK = False
            else:
                #print("I don't care")
                pass
        elif t == Gst.MessageType.TAG:
            return
            tag = message.parse_tag()
            count = tag.n_tags()
            print(count)
            for i in range(0, count):
                print(tag.nth_tag_name(i))
        elif t == Gst.MessageType.DURATION_CHANGED:
            return
            print("Duration changed!!")
            GObject.idle_add(self.update_duration)
        elif t == Gst.MessageType.STREAM_START:
            if self.DURATION == 0:
                print("Duration is 0!")
                GObject.idle_add(self.update_duration)

        elif t == Gst.MessageType.STREAM_STATUS:
            return
            print("STATUS:")
            print(message.parse_stream_status())
        else:
            print("Unexpected message!!", t)
        # print(message.type)
        # print(message.parse())
        return

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
        self.pipeline.add(self.filesrc)

        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message", self.msg)

        vsink = Gst.ElementFactory.make("autovideosink", None)
        self.pipeline.add(vsink)

        asink = Gst.ElementFactory.make("autoaudiosink", None)
        self.pipeline.add(asink)

        self.vsinkpad = vsink.get_static_pad("sink")
        self.asinkpad = asink.get_static_pad("sink")

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
        self.pipeline.set_state(Gst.State.READY)
        self.filesrc.set_property("uri", self.NEXT_FILE)
        self.pipeline.set_state(Gst.State.PLAYING)
        print('Calling channel now. LCT:', self.LAST_CHAPTER_TIME)
        # GObject.timeout_add(300, self.seek, self.LAST_CHAPTER_TIME)
        # GObject.timeout_add(300, self.update_duration)
        self.MUST_SEEK = True
        self.CHANGING_URI = False
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
        self.DURATION = d / 1000000000
        print("Duration:", self.DURATION)
        if self.on_duration is not None:
            self.on_duration(self.DURATION)
        return False  # To get the timeout interval to stop

    def seek(self, seek_time_secs):
        print("Asked to seek to: ", seek_time_secs)
        if abs(seek_time_secs - self.get_cur_time()) < 1:
            print("Not seeking < 1s")
            return
        seek_time_secs = min(seek_time_secs, max(self.DURATION - 1, 0))
        print("Seeking to", seek_time_secs)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH,
                                  seek_time_secs * Gst.SECOND)
        #   | Gst.SeekFlags.KEY_UNIT,
        return False  # To get the timeout interval to stop

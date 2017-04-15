#!/usr/bin/env python3
import threading
import time
import os
import random
import gi
import sys
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

GObject.threads_init()
Gst.init(None)

BASEPATH = "/home/david/git/old-tv/channels/3/0/"
exiting = False


class Main:
    LAST_CHAPTER_TIME = 0
    DURATION = 0

    def get_next_file(self):
        ret = "file://" + os.path.join(BASEPATH, random.choice(self.files))
        return ret

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

    def __init__(self, files):
        self.files = files
        self.mainloop = GObject.MainLoop()
        self.pipeline = Gst.Pipeline.new("mypipeline")
        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message", self.msg)

        self.filesrc = Gst.ElementFactory.make("uridecodebin", "filesrc")
        self.filesrc.connect("pad-added", self.decode_src_created)
        self.pipeline.add(self.filesrc)

        self.input_v = Gst.ElementFactory.make("input-selector", "isv")
        self.pipeline.add(self.input_v)

        vcaps = Gst.Caps.from_string("video/x-raw,width=576,height=432")
        vfilter = Gst.ElementFactory.make("capsfilter", "vfilter")
        vfilter.set_property("caps", vcaps)
        self.pipeline.add(vfilter)
        self.input_v.link(vfilter)

        vsink = Gst.ElementFactory.make("autovideosink", "vsink")
        self.pipeline.add(vsink)

        blankvideo = Gst.ElementFactory.make("videotestsrc", "snow")
        blankvideo.set_property("pattern", "snow")
        # blankvideo.set_property("is-live", True)
        self.pipeline.add(blankvideo)

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
        vfilter.link(vsink)
        blankvideo.link(self.input_v)
        blankaudio.link(self.input_a)

        tpl_v = self.input_v.get_pad_template("sink_%u")
        self.ivpad = self.input_v.request_pad(tpl_v, "sink_%u", None)

        tpl_a = self.input_a.get_pad_template("sink_%u")
        self.iapad = self.input_a.request_pad(tpl_a, "sink_%u", None)

        self.change_uri(self.get_next_file())

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
            if self.DURATION <= self.get_cur_time() + 5:
                # TODO: Avoid reentry
                GObject.idle_add(self.change_uri, self.get_next_file())
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
        GObject.timeout_add(100, self.seek, self.LAST_CHAPTER_TIME)
        GObject.timeout_add(300, self.update_duration)

    def get_cur_time(self):
        # delta = (self.filesrc.get_clock().get_time() - self.INITIAL_TIME)
        _, delta = self.pipeline.query_position(Gst.Format.TIME)
        return delta / 1000000000

    def snow(self):
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

    def change_uri(self, uri):
        self.LAST_CHAPTER_TIME = 0
        self.DURATION = 0
        self.pipeline.set_state(Gst.State.READY)
        self.filesrc.set_property("uri", uri)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.channel()

    def update_duration(self):
        _, d = self.filesrc.query_duration(Gst.Format.TIME)
        self.DURATION = d / 1000000000
        print("Duration:", self.DURATION)
        return False  # To get the timeout interval to stop

    def seek(self, seek_time_secs):
        seek_time_secs = min(seek_time_secs, max(self.DURATION - 1, 0))
        print("Seeking to", seek_time_secs)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH,
                                  seek_time_secs * Gst.SECOND)
        #   | Gst.SeekFlags.KEY_UNIT,
        return False  # To get the timeout interval to stop


def control(target):
    global exiting
    data = ""
    while data != "q":
        data = input()
        if data == "next" or data == "n":
            target.change_uri(target.get_next_file())
        elif data == "snow" or data == "s":
            target.snow()
        elif data == "channel" or data == "c":
            target.channel()
        else:
            try:
                target.seek(float(data))
            except Exception:
                print("Exiting control")
                break
    exiting = True


def main():
    files = [f for f in os.listdir(BASEPATH)
             if os.path.isfile(os.path.join(BASEPATH, f)) and
             (f.endswith("mp4") or f.endswith("mkv"))]

    start = Main(files)
    t1 = threading.Thread(target=control, args=(start,))
    t1.start()
    start.run()
    t1.join()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import threading
import os
import random
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

GObject.threads_init()

Gst.init(None)

BASEPATH = "/home/david/Downloads/SA86/"


class Main:

    def get_next_file(self):
        ret = "file://" + os.path.join(BASEPATH, random.choice(self.files))
        return ret

    def msg(self, bus, message):
        print(message.type)
        # print(message.parse())
        pass

    def __init__(self, files):
        self.files = files
        self.mainloop = GObject.MainLoop()
        self.pipeline = Gst.Pipeline.new("mypipeline")
        self.pipeline.bus.add_signal_watch()
        self.pipeline.bus.connect("message", self.msg)


        self.filesrc = Gst.ElementFactory.make("uridecodebin", "filesrc")
        self.filesrc.set_property("uri", "file:///home/david/Downloads/SA86/TO4-C26.mkv")
        self.filesrc.connect("pad-added", self.decode_src_created)
        self.pipeline.add(self.filesrc)

        self.input_v = Gst.ElementFactory.make("input-selector", "isv")
        self.pipeline.add(self.input_v)


        self.vsink = Gst.ElementFactory.make("autovideosink", "vsink")
        self.pipeline.add(self.vsink)


        self.blankvideo = Gst.ElementFactory.make("videotestsrc", "snow")
        self.blankvideo.set_property("pattern", 1)
        #self.blankvideo.set_property("is-live", True)
        self.pipeline.add(self.blankvideo)


        # vcaps = Gst.Caps.from_string("video/x-raw,width=576,height=432")
        # vfilter = Gst.ElementFactory.make("capsfilter", "vfilter")
        # vfilter.set_property("caps", vcaps)

        self.blankaudio = Gst.ElementFactory.make("audiotestsrc", "noise")
        self.blankaudio.set_property("wave", "white-noise")
        self.blankaudio.set_property("volume", 0.02)
        #self.blankaudio.set_property("is-live", True)
        self.pipeline.add(self.blankaudio)

        self.input_a = Gst.ElementFactory.make("input-selector", "isa")
        self.pipeline.add(self.input_a)

        self.asink = Gst.ElementFactory.make("autoaudiosink", "asink")
        self.pipeline.add(self.asink)

        self.input_a.link(self.asink)
        self.input_v.link(self.vsink)
        self.blankvideo.link(self.input_v)
        self.blankaudio.link(self.input_a)

        tpl_v = self.input_v.get_pad_template("sink_%u")
        self.ivpad = self.input_v.request_pad(tpl_v, "sink_%u", None)

        tpl_a = self.input_a.get_pad_template("sink_%u")
        self.iapad = self.input_a.request_pad(tpl_a, "sink_%u", None)

    # handler taking care of linking the decoder's newly created source pad to the sink
    def decode_src_created(self, element, pad):
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
        if self.filesrc.get_state != Gst.State.PLAYING:
            self.filesrc.set_state(Gst.State.PLAYING)

        snowpad = self.input_v.get_static_pad('sink_%d' % 1)
        self.input_v.set_property('active-pad', snowpad)

        snowpad = self.input_a.get_static_pad('sink_%d' % 1)
        self.input_a.set_property('active-pad', snowpad)

    def get_cur_time(self):
        #delta = (self.filesrc.get_clock().get_time() - self.INITIAL_TIME)
        _, delta = self.pipeline.query_position(Gst.Format.TIME)
        return delta / 1000000000

    def snow(self):
        # help(self.filesrc)
        # help(Gst.Format)
        # help(self.input_v.get_property('active_pad'))

        snowpad = self.input_v.get_static_pad('sink_%d' % 0)
        self.input_v.set_property('active-pad', snowpad)

        snowpad = self.input_a.get_static_pad('sink_%d' % 0)
        self.input_a.set_property('active-pad', snowpad)

        if self.filesrc.get_state != Gst.State.READY:
            self.filesrc.set_state(Gst.State.READY)

    # running the shit
    def run(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop.run()

    def change_uri(self):
        nf = self.get_next_file()
        print(nf)
        self.pipeline.set_state(Gst.State.READY)
        self.filesrc.set_property("uri", nf)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.channel()

    def seek(self, seek_time_secs):
        # self.filesrc.seek_simple(Gst.Format.TIME,
        #                          Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
        #                          seek_time_secs * Gst.SECOND)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH,
                                  seek_time_secs * Gst.SECOND)


def control(target):
    data = ""
    while data != "q":
        data = input()
        if data == "next" or data == "n":
            target.change_uri()
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

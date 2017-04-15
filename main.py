#!/usr/bin/python3
from player import Player
import os
import threading
import random
import channel_indexer as ci
from pprint import pprint


class TrackProgram():
    BASEPATH = "/home/david/git/old-tv/channels/"
    ADS_PATH = "/home/david/git/old-tv/ads/"
    guide = {}
    channel = 3
    program = 0

    def get_next_file(self):
        # FIXME: Not random
        files = self.guide['channels'][self.channel][self.program]
        ret = os.path.join(self.BASEPATH,
                           str(self.channel),
                           str(self.program),
                           random.choice(files))
        return "file://" + ret

    def get_random_ad(self):
        return "file://" + os.path.join(self.ADS_PATH,
                                        random.choice(self.guide['ads']))

    def control(self):
        data = ""
        while data != "q":
            data = input()
            if data == "next" or data == "n":
                self.player.change_uri(self.player.get_next_file())
            elif data == "snow" or data == "s":
                self.player.snow()
            elif data == "channel" or data == "c":
                self.player.channel()
            elif data.startswith("uri") or data == "u":
                self.player.set_next_file(self.get_random_ad())
            else:
                try:
                    self.player.seek(float(data))
                except Exception:
                    print("Exiting control")
                    break

    def finished_playing(self):
        if self.current_file['type'] == 'ad':
            self.player.set_next_file(self.get_next_file())
        else:
            self.player.set_next_file(self.get_random_ad())

    def __init__(self):
        self.guide = ci.index()
        self.current_file = {}
        # pprint(channels)
        self.player = Player(on_finished=self.finished_playing)
        self.player.set_next_file(self.get_next_file())
        self.player.change_uri()

        t1 = threading.Thread(target=self.control)
        t1.start()
        self.player.run()
        t1.join()


if __name__ == "__main__":
    t = TrackProgram()

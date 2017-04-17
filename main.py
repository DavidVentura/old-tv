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
    status = {}
    # status[channel] = {
    #   type: 'ad', file: '...',
    #   chapterIndex: 0, programIndex: 0,
    #   time: 100s
    # }

    def get_cur_file(self):
        s = self.get_current_status()
        ret = ""
        if s['curType'] == 'ad':
            s['curFileIndex'] = s['curFileIndex'] % len(self.guide['ads'])
            ret = os.path.join(self.ADS_PATH,
                               self.guide['ads'][s['curFileIndex']])
        else:
            self.program = self.program % len(self.guide['channels'][self.channel])
            s['curFileIndex'] = s['curFileIndex'] % len(self.guide['channels'][self.channel][self.program])
            ret = os.path.join(self.BASEPATH,
                               str(self.channel),
                               str(self.program),
                               self.guide['channels'][self.channel][self.program][s['curFileIndex']])

        return "file://" + ret

    def get_next_file(self):
        if self.get_current_status()['curType'] == 'ad':
            self.player.set_next_file(self.get_next_chapter())
        else:
            self.player.set_next_file(self.get_random_ad())

    def get_next_chapter(self):
        files = self.guide['channels'][self.channel][self.program]
        ret = os.path.join(self.BASEPATH,
                           str(self.channel),
                           str(self.program),
                           files[self.get_current_status()['chapterIndex']])
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
            elif data == "+":
                self.set_channel(self.channel + 1)
            elif data == "-":
                self.set_channel(self.channel - 1)
            else:
                try:
                    self.player.seek(float(data))
                except Exception:
                    print("Exiting control")
                    break

    def get_current_status(self):
        # TODO: Return valid data on incomplete input
        return self.status[self.channel]

    def set_current_status(self, k, v):
        self.status[self.channel][k] = v

    def finished_playing(self):
        self.player.change_uri(self.player.get_next_file())

    def load_status(self):
        # TODO: Load this from a file
        return {
                2: {
                    'curType': 'ad',
                    'curFileIndex': 5,
                    'curFileTime': 10,
                    'curFileDuration': 40,
                    'lastChapterIndex': 3,
                    'lastProgramIndex': 0,
                   },
                3: {
                    'curType': 'program',
                    'curFileIndex': 5,
                    'curFileTime': 10,
                    'curFileDuration': 40,
                    'lastChapterIndex': 3,
                    'lastProgramIndex': 0,
                   },
                5: {
                    'curType': 'program',
                    'curFileIndex': 5,
                    'curFileTime': 10,
                    'curFileDuration': 40,
                    'lastChapterIndex': 3,
                    'lastProgramIndex': 0,
                   },
                }

    def set_channel(self, channel):
        self.channel = min(max(channel, 1), 12)
        print("New channel:", self.channel)
        if self.channel not in self.valid_channels:
            self.player.snow()
            return

        self.player.set_next_file(self.get_cur_file())
        cs = self.get_current_status()
        self.player.change_uri(start_time=cs['curFileTime'],
                               duration=cs['curFileDuration'])

    def __init__(self):
        self.guide = ci.index()
        self.valid_channels = self.guide['channels'].keys()

        self.status = self.load_status()
        self.player = Player(on_finished=self.finished_playing)
        self.set_channel(3)  # FIXME: Must call a valid channel so pads link
        self.set_channel(4)

        t1 = threading.Thread(target=self.control)
        t1.start()
        self.player.run()
        t1.join()


if __name__ == "__main__":
    t = TrackProgram()
